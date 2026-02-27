from rest_framework import serializers
from .models import Products, Sizes, Colors, ProductPhoto, VariantProduct

class ProductsSerializer(serializers.ModelSerializer):

    def validate_price(self, value):
        if value <= 0:
            raise serializers.ValidationError(
                detail='el precio debe ser mayor a 0',
                code='precio_invalido',
            )
        return value
    
    class Meta:
        model = Products
        fields = '__all__'
        extra_kwargs = {
            'id_product':{'read_only':True}
        }

class PatchStateProductsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Products
        fields = ['is_active']

class ColorsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Colors
        fields = '__all__'
        extra_kwargs = {
            'id_color':{'read_only':True}
        }

class SizesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Sizes
        fields = '__all__'
        extra_kwargs = {
            'id_size':{'read_only':True}
        }

class ProductsPhotosSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductPhoto
        fields = '__all__'
        extra_kwargs = {
            'id':{'read_only':True}
        }

class VariantProductsSerializer(serializers.ModelSerializer):
    def validate_sku(self, value):
        if VariantProduct.objects.filter(sku=value).exists():
            raise serializers.ValidationError(
                detail='este SKU ya existe',
                code='sku_exists'
            )
        return value
    class Meta:
        model = VariantProduct
        fields = '__all__'
        extra_kwargs = {
            'id_variant':{'read_only':True}
        }