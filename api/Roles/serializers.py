from rest_framework import serializers
from .models import Roles

class RolesSerializers(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'
        extra_kwargs = {
            'idRol': {'read_only':True},
            'created_at': {'read_only':True},
            'updated_at': {'read_only':True},
        }
