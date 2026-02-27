from rest_framework import serializers
from .models import Inventory

class InventorySerializers(serializers.ModelSerializer):
    def validate_stock(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                detail='el stock no puede ser negativo',
                code='stock_invalid'
            )
        return value
    class Meta:
        model = Inventory
        fields = '__all__'
        extra_kwargs = {
            'id_inventory':{'read_only':True},
            'updated_at':{'read_only':True},
        }

class AdjustStockSerializer(serializers.Serializer):
    amount = serializers.IntegerField()

    def validate_stock(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                detail='el stock no puede ser negativo',
                code='invalid_stock'
            )
        return value