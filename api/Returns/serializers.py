from rest_framework import serializers
from .models import Returns, ReturnDetail, Changes, ChangesDetails
from api.Sales.models import Sales, SalesDetail
import decimal
from django.db import transaction
from api.Inventory.services import  out_stock, add_stock
import logging

logger = logging.getLogger(__name__)

IVA = decimal.Decimal('0.19')


# ==================== SERIALIZERS PARA DEVOLUCIONES ====================

class ReturnDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = ReturnDetail
        fields = '__all__'
        extra_kwargs = {
            'id_detail': {'read_only': True},
            'subtotal': {'read_only': True},
            'return_id': {'read_only': True}
        }


class ReturnsSerializer(serializers.ModelSerializer):
    details = ReturnDetailSerializer(many=True, source='return_detail')
    sale_number = serializers.CharField(source='sale.number_sale', read_only=True)
    state_name = serializers.CharField(source='state.name_state', read_only=True)
    
    class Meta:
        model = Returns
        fields = '__all__'
        extra_kwargs = {
            'return_number': {'read_only': True},
            'return_date': {'read_only': True},
            'total': {'read_only': True},
            'balance_in_favor': {'read_only': True},
            'difference_to_pay': {'read_only': True}
        }

    def validate_details(self, details):
        if not details:
            raise serializers.ValidationError(
                detail='sin detalles de devolución',
                code='not_details'
            )
        return details
    
    def validate(self, data):
        """Validar que la venta exista y esté en estado válido para devolución"""
        sale = data.get('sale')
        if sale and sale.state.name_state in ['anulada', 'devuelta']:
            raise serializers.ValidationError(
                detail=f'No se puede hacer devolución de una venta {sale.state.name_state}',
                code='invalid_sale_state'
            )
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        details_data = validated_data.pop('return_detail')
        
        # Crear devolución con valores iniciales
        return_obj = Returns.objects.create(
            **validated_data,
            total=decimal.Decimal('0'),
            balance_in_favor=decimal.Decimal('0'),
            difference_to_pay=decimal.Decimal('0')
        )
        
        logger.info(f'creando devolución: {return_obj.id_return}, número: {return_obj.return_number}')

        total_return = decimal.Decimal('0')

        for detail in details_data:
            variant = detail['variant']
            quantity = detail['quantity']
            
            # Obtener el precio unitario del detalle de venta original
            try:
                sales_detail = SalesDetail.objects.get(sale=return_obj.sale, variant=variant)
                unit_price = sales_detail.unit_price
            except SalesDetail.DoesNotExist:
                logger.error(f'no se encontró el detalle de venta para variante: {variant.id}')
                raise serializers.ValidationError(
                    detail=f'La variante {variant.sku} no se encontró en la venta original',
                    code='variant_not_in_sale'
                )
            except SalesDetail.MultipleObjectsReturned:
                logger.warning(f'múltiples detalles encontrados para variante: {variant.id}')
                sales_detail = SalesDetail.objects.filter(sale=return_obj.sale, variant=variant).first()
                unit_price = sales_detail.unit_price
            
            subtotal_price = decimal.Decimal(str(unit_price)) * quantity

            ReturnDetail.objects.create(
                return_id=return_obj,
                variant=variant,
                quantity=quantity,
                subtotal=subtotal_price
            )

            # Devolver stock al inventario
            add_stock(variant, quantity)
            logger.info(f'stock incrementado en cantidad: {quantity}')
            total_return += subtotal_price
        
        # Calcular totales de la devolución
        return_obj.total = total_return
        
        # Calcular balance a favor o diferencia a pagar
        sale_total = return_obj.sale.total
        if total_return >= sale_total:
            return_obj.balance_in_favor = total_return - sale_total
            return_obj.difference_to_pay = decimal.Decimal('0')
        else:
            return_obj.balance_in_favor = decimal.Decimal('0')
            return_obj.difference_to_pay = sale_total - total_return
        
        return_obj.save()
        
        # Marcar la venta como procesando devolución
        sale = return_obj.sale
        sale.return_executing = True
        sale.save()
        
        return return_obj


# ==================== SERIALIZERS PARA CAMBIOS ====================

class ChangesDetailsSerializer(serializers.ModelSerializer):
    class Meta:
        model = ChangesDetails
        fields = '__all__'
        extra_kwargs = {
            'id': {'read_only': True},
            'change': {'read_only': True}
        }


class ChangesSerializer(serializers.ModelSerializer):
    details = ChangesDetailsSerializer(many=True, source='change_detail')
    sale_number = serializers.CharField(source='sale.number_sale', read_only=True)
    state_name = serializers.CharField(source='state.name_state', read_only=True)
    
    class Meta:
        model = Changes
        fields = '__all__'
        extra_kwargs = {
            'change_number': {'read_only': True},
            'stock_applied': {'read_only': True},
            'return_applied': {'read_only': True}
        }

    def validate_details(self, details):
        if not details:
            raise serializers.ValidationError(
                detail='sin detalles de cambio',
                code='not_details'
            )
        return details
    
    def validate(self, data):
        """Validar que la venta exista y esté en estado válido para cambio"""
        sale = data.get('sale')
        if sale and sale.state.name_state in ['anulada', 'devuelta']:
            raise serializers.ValidationError(
                detail=f'No se puede hacer cambio de una venta {sale.state.name_state}',
                code='invalid_sale_state'
            )
        return data
    
    @transaction.atomic
    def create(self, validated_data):
        details_data = validated_data.pop('change_detail')
        
        # Crear cambio
        change = Changes.objects.create(**validated_data)
        
        logger.info(f'creando cambio: {change.id_change}, número: {change.change_number}')

        for detail in details_data:
            variant_returned = detail['variant_returned']
            variant_delivered = detail['variant_delivered']

            ChangesDetails.objects.create(
                change=change,
                variant_returned=variant_returned,
                variant_delivered=variant_delivered
            )

            # Aplicar cambios de stock
            if not change.stock_applied:
                # Devolver al inventario la variante recibida
                add_stock (variant_returned, 1)  # Asumiendo cantidad de 1
                logger.info(f'stock incrementado para variante devuelta: {variant_returned.id_variant}')
                
                # Restar del inventario la variante entregada
                out_stock(variant_delivered, 1)
                logger.info(f'stock reducido para variante entregada: {variant_delivered.id_variant}')
        
        change.stock_applied = True
        change.save()
        
        return change