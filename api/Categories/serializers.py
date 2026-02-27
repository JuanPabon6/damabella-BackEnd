from rest_framework import serializers
from .models import Categories

class CategoriesSerializers(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = '__all__'
        extra_kwargs = {
            'id_category': {'read_only':True},
        }

class PatchStateCategoriesSerializers(serializers.ModelSerializer):
    class Meta:
        model = Categories
        fields = ['is_active']
    def validate(self, attrs):
        if set(self.initial_data.keys()) != {'is_active'}:
            raise serializers.ValidationError("Solo se puede enviar el campo is_active")
        return attrs