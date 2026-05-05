from rest_framework import serializers
from .models import Purchases, PurchaseDetail
from django.db import transaction
from api.Inventory.models import Inventory
from api.Products.models import VariantProduct
from decimal import Decimal
from api.Inventory.services import add_stock, out_stock


class PurchaseDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = PurchaseDetail
        fields = '__all__'
        extra_kwargs = {
            'id_detail':{'read_only':True},
            #purchase se coloca read_only para manejarlo internamente y no tomar campos  enviados del front
            'purchase':{'read_only':True},
            'subtotal':{'read_only':True}
        }
IVA = Decimal('0.19')
class PurchasesSerializer(serializers.ModelSerializer):
    details = PurchaseDetailSerializer(many=True, source='detail_purchase')
    provider_name = serializers.CharField(source='provider.name', read_only=True)
    state_name = serializers.CharField(source='states.name_state', read_only=True)

    def validate_details(self, details):
        if not details:
            raise serializers.ValidationError(code='not_details', detail='sin detalles de compra')
        return details
    
    @transaction.atomic
    def create(self, validated_data):
        details_data = validated_data.pop('detail_purchase')
        purchase = Purchases.objects.create(**validated_data)

        subtotal_purchase = Decimal('0')

        for details in details_data:
            variant       = details['variant']
            quantity      = details['quantity']
            purchase_price = details['purchase_price']
            sales_price   = details['sales_price']
            subtotal_detail = Decimal(str(purchase_price)) * quantity

            PurchaseDetail.objects.create(
                purchase = purchase,
                variant = variant,
                quantity = quantity,
                purchase_price = purchase_price,
                sales_price = sales_price,
                subtotal = subtotal_detail
            )

            add_stock(variant,quantity)
            subtotal_purchase += subtotal_detail
        purchase.subtotal = subtotal_purchase
        purchase.iva = subtotal_purchase * IVA
        purchase.total = subtotal_purchase + purchase.iva
        purchase.save()
        return purchase

    @transaction.atomic
    def update(self, instance, validated_data):
        ESTADOS_BLOQUEADOS = ['Entregado', 'Cancelado']
        if instance.state.name_state in ESTADOS_BLOQUEADOS:
            raise serializers.ValidationError(
                detail=f'No se puede modificar una compra en estado {instance.state.name_state}',
                code='purchase_locked'
            )
        
        details_data = validated_data.pop('detail_purchase', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if details_data is not None:
            for old_detail in instance.detail_purchase.all():
                out_stock(old_detail.variant, old_detail.quantity)

            instance.detail_purchase.all().delete()

            subtotal_compra = Decimal('0')

            for detail in details_data:
                variant         = detail['variant']
                quantity        = detail['quantity']
                purchase_price  = detail['purchase_price']
                sales_price     = detail['sales_price']
                subtotal_detail = Decimal(str(purchase_price)) * quantity

                PurchaseDetail.objects.create(
                    purchase       = instance,
                    variant        = variant,
                    quantity       = quantity,
                    purchase_price = purchase_price,
                    sales_price    = sales_price,
                    subtotal       = subtotal_detail
                )

                add_stock(variant, quantity)
                subtotal_compra += subtotal_detail

            instance.subtotal = subtotal_compra
            instance.iva      = subtotal_compra * IVA
            instance.total    = instance.subtotal + instance.iva

        instance.save()
        return instance
            

    class Meta:
        model = Purchases
        fields = '__all__'
        extra_kwargs = {
            'id_purchase':{'read_only':True},
            'purchase_date':{'read_only':True},
            'registration_date':{'read_only':True},
            'purchase_number':{'read_only':True},
            'subtotal':{'read_only':True},
            'iva':{'read_only':True},
            'total':{'read_only':True}
        }