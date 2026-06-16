from rest_framework import serializers
from .models import Sales, SalesDetail
from api.Orders.models import Orders
from api.States.models import States
import decimal
from django.db import transaction
from api.Inventory.services import out_stock
import logging

logger = logging.getLogger(__name__)

class SalesDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = SalesDetail
        fields = '__all__'
        extra_kwargs = {
            'id_detail': {'read_only': True},
            'subtotal': {'read_only': True},
            'creation_date': {'read_only': True},
            'sale': {'read_only': True}
        }


class SalesSerializer(serializers.ModelSerializer):
    details = SalesDetailsSerializer(many=True, source='sale_detail')
    client_name = serializers.CharField(source='client.name_client', read_only=True)
    state_name = serializers.CharField(source='state.name_state', read_only=True)
    number_pedido = serializers.CharField(source='order.number_order', read_only=True)
    
    class Meta:
        model = Sales
        fields = '__all__'
        extra_kwargs = {
            'number_sale': {'read_only': True},
            'date_sale': {'read_only': True},
            'subtotal': {'read_only': True},
            'iva': {'read_only': True},
            'total': {'read_only': True},
            'output_executing': {'read_only': True},
            'return_executing': {'read_only': True}
        }

    def validate_details(self, details):
        if not details:
            raise serializers.ValidationError(
                detail='sin detalles de venta',
                code='not_details'
            )
        return details
    
    @transaction.atomic
    def create(self, validated_data):
        details_data = validated_data.pop('sale_detail')

        # Soportar id_pedido opcional enviado desde el front
        order_instance = None
        if 'id_pedido' in validated_data:
            id_pedido = validated_data.pop('id_pedido')
            try:
                order_instance = Orders.objects.get(pk=id_pedido)
                validated_data['order'] = order_instance
            except Orders.DoesNotExist:
                raise serializers.ValidationError(detail=f'El pedido con id {id_pedido} no existe', code='order_not_found')

        # Crear venta con valores iniciales
        sale = Sales.objects.create(
            **validated_data,
            subtotal=decimal.Decimal('0'),
            iva=decimal.Decimal('0'),
            total=decimal.Decimal('0')
        )
        
        logger.info(f'creando venta: {sale.id_sale}, con numero: {sale.number_sale}')

        subtotal_sale = decimal.Decimal('0')
        iva_sale = decimal.Decimal('0')

        for detail in details_data:
            variant = detail['variant']
            quantity = detail['quantity']
            unit_price = detail['unit_price']
            subtotal_price = decimal.Decimal(str(unit_price)) * quantity
            iva_percentage = decimal.Decimal(str(variant.product.iva.percentage)) / decimal.Decimal('100')
            iva_detail = subtotal_price * iva_percentage

            SalesDetail.objects.create(
                sale=sale,
                variant=variant,
                quantity=quantity,
                unit_price=unit_price,
                subtotal=subtotal_price
            )

            out_stock(variant, quantity)
            logger.info(f'stock reducido en cantidad: {quantity}')
            subtotal_sale += subtotal_price
            iva_sale += iva_detail
        
        sale.subtotal = subtotal_sale
        sale.iva = iva_sale
        sale.total = sale.subtotal + sale.iva
        sale.save()
        
        # Si la venta se creó a partir de un pedido, marcar el pedido como convertido
        if order_instance is not None:
            try:
                convertido_state = States.objects.filter(name_state__iexact='Convertido').first()
                if convertido_state:
                    order_instance.state = convertido_state
                    order_instance.save(update_fields=['state'])
                else:
                    logger.warning('No se encontró el estado "Convertido" en la tabla States; se omite el cambio de estado del pedido')
            except Exception as e:
                logger.error(f'Error al actualizar el estado del pedido {order_instance.id_order}: {e}', exc_info=True)

        return sale
        
    @transaction.atomic
    def update(self, instance, validated_data):
        ESTADOS_BLOQUEADOS = ['pagada', 'entregada', 'anulada', 'devuelta']
        
        if instance.state.name_state in ESTADOS_BLOQUEADOS:
            raise serializers.ValidationError(
                detail=f'No se puede modificar una venta en estado {instance.state.name_state}',
                code='sale_locked'
            )
        
        details_data = validated_data.pop('sale_detail', None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        subtotal_sale = decimal.Decimal('0')
        iva_sale = decimal.Decimal('0')

        if details_data is not None:
            for detail in details_data:
                variant = detail['variant']
                quantity = detail['quantity']
                unit_price = detail['unit_price']
                subtotal_price = decimal.Decimal(str(unit_price)) * quantity
                iva_percentage = decimal.Decimal(str(variant.product.iva.percentage)) / decimal.Decimal('100')
                iva_detail = subtotal_price * iva_percentage

                SalesDetail.objects.create(
                    sale=instance,
                    variant=variant,
                    quantity=quantity,
                    unit_price=unit_price,
                    subtotal=subtotal_price
                )

                out_stock(variant, quantity)
                subtotal_sale += subtotal_price
                iva_sale += iva_detail

            instance.subtotal = subtotal_sale
            instance.iva = iva_sale
            instance.total = instance.subtotal + instance.iva

        instance.save()
        return instance