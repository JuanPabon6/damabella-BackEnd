from rest_framework import serializers
from .models import Orders,OrdersDetail, PaymentMethods
from django.db import transaction
from decimal import Decimal

class OrderDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model=OrdersDetail
        fields='__all__'
        extra_kwargs={
            'id_detail':{'read_only':True},
            'order':{'read_only':True},
            'subtotal':{'read_only':True}
        }


IVA = Decimal('0.19')
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

        for detail in details_data:
            variant  = detail['variant']
            quantity = detail['quantity']
            sales_price = variant.product.price  
            subtotal_detail = Decimal(str(sales_price)) * quantity

            OrdersDetail.objects.create(
                order       = order,
                variant     = variant,
                quantity    = quantity,
                sales_price = sales_price,
                subtotal    = subtotal_detail
            )
            subtotal_order += subtotal_detail

        order.subtotal = subtotal_order
        order.iva      = subtotal_order * IVA
        order.total    = subtotal_order + order.iva
        order.save()
        return order

    class Meta:
        model = Orders
        fields = '__all__'
        extra_kwargs = {
            'id_order':    {'read_only': True},
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