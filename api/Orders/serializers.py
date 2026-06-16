from rest_framework import serializers
from .models import Orders, OrdersDetail, PaymentMethods
from django.db import transaction
from decimal import Decimal

class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrdersDetail
        fields = '__all__'
        extra_kwargs = {
            'id_detail': {'read_only': True},
            'order': {'read_only': True},
            'subtotal': {'read_only': True}
        }


class OrdersSerializers(serializers.ModelSerializer):
    detail = OrderDetailSerializer(many=True, source='detail_order')
    client_name = serializers.CharField(source='client.name', read_only=True)
    state_name = serializers.CharField(source='state.name_state', read_only=True)
    payment_method_name = serializers.CharField(source='payment_method.name', read_only=True)

    @transaction.atomic
    def create(self, validated_data):
        details_data = validated_data.pop('detail_order')
        order = Orders.objects.create(**validated_data)

        subtotal_order = Decimal('0')
        iva_order = Decimal('0')

        for detail in details_data:
            variant = detail['variant']
            quantity = detail['quantity']
            
            # Dejamos la lógica nueva de tu rama (juanjo): El precio viene del producto
            sales_price = variant.product.price
            
            subtotal_detail = Decimal(str(sales_price)) * quantity
            iva_percentage = Decimal(str(variant.product.iva.percentage)) / Decimal('100')
            iva_detail = subtotal_detail * iva_percentage

            OrdersDetail.objects.create(
                order=order,
                variant=variant,
                quantity=quantity,
                sales_price=sales_price,
                subtotal=subtotal_detail
            )
            subtotal_order += subtotal_detail
            iva_order += iva_detail

        order.subtotal = subtotal_order
        order.iva = iva_order
        order.total = subtotal_order + order.iva
        order.save()
        return order
    
    def update(self, instance, validated_data):
        # 1. Sacamos los datos anidados de los detalles del payload validado
        details_data = validated_data.pop('detail_order', None)

        # 2. Actualizamos los campos normales del pedido
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()

        # 3. Procesamos los detalles anidados si vienen en el PUT
        if details_data is not None:
            # Borramos los detalles viejos y registramos los nuevos del carrito
            instance.detail_order.all().delete()
            
            from api.Orders.models import OrdersDetail
            for detail_dict in details_data:
                OrdersDetail.objects.create(order=instance, **detail_dict)

        return instance

    class Meta:
        model = Orders
        fields = '__all__'
        extra_kwargs = {
            'id_order':     {'read_only': True},
            'order_date':  {'read_only': True},
            'number_order':{'read_only': True},
            'subtotal':    {'read_only': True},
            'iva':         {'read_only': True},
            'total':       {'read_only': True},
        }

class PaymentMethodsSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaymentMethods
        fields = '__all__'