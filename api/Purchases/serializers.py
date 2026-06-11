from rest_framework import serializers
from .models import Purchases, PurchaseDetail, Iva
from django.db import transaction
from api.Inventory.models import Inventory
from api.Products.models import VariantProduct
from decimal import Decimal, InvalidOperation
from api.Inventory.services import add_stock, out_stock


def clean_decimal(value):
    if value is None:
        return None
    if isinstance(value, Decimal):
        return value
    text = str(value).strip().replace(' ', '')
    if text.count(',') == 1 and text.count('.') > 0:
        text = text.replace('.', '').replace(',', '.')
    elif text.count('.') > 1:
        text = text.replace('.', '')
    elif text.count(',') > 1:
        text = text.replace(',', '')
    elif ',' in text:
        text = text.replace(',', '.')
    try:
        return Decimal(text)
    except InvalidOperation:
        raise serializers.ValidationError(f'Valor numérico inválido: {value}')


def clean_int(value):
    if isinstance(value, int):
        return value
    text = str(value).strip().replace(' ', '')
    text = text.replace('.', '').replace(',', '')
    return int(text)


class PurchaseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseDetail
        fields = '__all__'
        extra_kwargs = {
            'id_detail': {'read_only': True},
            # purchase se coloca read_only para manejarlo internamente y no tomar campos enviados del front
            'purchase': {'read_only': True},
            'subtotal': {'read_only': False}
        }

class PurchasesSerializer(serializers.ModelSerializer):
    details = PurchaseDetailSerializer(many=True, source='detail_purchase')
    provider_name = serializers.CharField(source='provider.name', read_only=True)

    def validate_details(self, details):
        if not details:
            raise serializers.ValidationError(code='not_details', detail='sin detalles de compra')
        return details
    
    @transaction.atomic
    def create(self, validated_data):
        details_data = validated_data.pop('detail_purchase')
        purchase_subtotal = clean_decimal(validated_data.pop('subtotal', None))
        purchase_total = clean_decimal(validated_data.pop('total', None))
        validated_data.pop('iva', None)

        purchase = Purchases.objects.create(
            **validated_data,
            subtotal=Decimal('0'),
            total=Decimal('0')
        )

        subtotal_compra = Decimal('0')
        total_compra = Decimal('0')

        for detail in details_data:
            variant = detail['variant']
            quantity = clean_int(detail['quantity'])
            purchase_price = clean_decimal(detail['purchase_price'])
            sales_price = clean_decimal(detail['sales_price'])
            subtotal_item = purchase_price * quantity
            
            # Obtener IVA del producto/variante
            iva_percentage = clean_decimal(variant.product.iva.percentage)
            # Si el porcentaje es mayor a 1, asumir que es 19 (no 0.19)
            if iva_percentage > 1:
                iva_percentage = iva_percentage / Decimal('100')
            
            iva_item = subtotal_item * iva_percentage

            PurchaseDetail.objects.create(
                purchase=purchase,
                variant=variant,
                quantity=quantity,
                purchase_price=purchase_price,
                sales_price=sales_price,
                subtotal=subtotal_item
            )

            add_stock(variant, quantity)
            subtotal_compra += subtotal_item
            total_compra += (subtotal_item + iva_item)

        purchase.subtotal = purchase_subtotal or subtotal_compra
        purchase.total = purchase_total or total_compra
        purchase.save()
        return purchase

    @transaction.atomic
    def update(self, instance, validated_data):        
        details_data = validated_data.pop('detail_purchase', None)
        purchase_subtotal = clean_decimal(validated_data.pop('subtotal', None))
        purchase_total = clean_decimal(validated_data.pop('total', None))
        validated_data.pop('iva', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if details_data is not None:
            for old_detail in instance.detail_purchase.all():
                out_stock(old_detail.variant, old_detail.quantity)

            instance.detail_purchase.all().delete()

            subtotal_compra = Decimal('0')
            total_compra = Decimal('0')

            for detail in details_data:
                variant = detail['variant']
                quantity = clean_int(detail['quantity'])
                purchase_price = clean_decimal(detail['purchase_price'])
                sales_price = clean_decimal(detail['sales_price'])
                subtotal_item = purchase_price * quantity
                
                # Obtener IVA del producto/variante
                iva_percentage = clean_decimal(variant.product.iva.percentage)
                # Si el porcentaje es mayor a 1, asumir que es 19 (no 0.19)
                if iva_percentage > 1:
                    iva_percentage = iva_percentage / Decimal('100')
                
                iva_item = subtotal_item * iva_percentage

                PurchaseDetail.objects.create(
                    purchase=instance,
                    variant=variant,
                    quantity=quantity,
                    purchase_price=purchase_price,
                    sales_price=sales_price,
                    subtotal=subtotal_item
                )

                add_stock(variant, quantity)
                subtotal_compra += subtotal_item
                total_compra += (subtotal_item + iva_item)

            instance.subtotal = purchase_subtotal or subtotal_compra
            instance.total = purchase_total or total_compra

        instance.save()
        return instance
            

    class Meta:
        model = Purchases
        fields = '__all__'
        extra_kwargs = {
            'id_purchase': {'read_only': True},
            'purchase_date': {'read_only': True},
            'registration_date': {'read_only': True},
            'purchase_number': {'read_only': True},
            'subtotal': {'read_only': False},
            'iva': {'read_only': True},
            'total': {'read_only': False}
        }

class IvaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Iva
        fields = '__all__'
        extra_kwargs = {
            'id':{'read_only':True}
        }