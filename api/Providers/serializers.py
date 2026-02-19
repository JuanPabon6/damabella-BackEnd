from rest_framework import serializers
from .models import Providers

class ProvidersSerializers(serializers.ModelSerializer):
    class Meta:
        model = Providers
        fields = '__all__'
        extra_kwargs = {
            'created_at':{'read_only':True},
            'updated_at':{'read_only':True},
        }