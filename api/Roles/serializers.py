from rest_framework import serializers
from .models import Roles, Permissions

class RolesSerializers(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = '__all__'
        extra_kwargs = {
            'idRol': {'read_only':True},
            'created_at': {'read_only':True},
            'updated_at': {'read_only':True},
        }

class PatchStateRolesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Roles
        fields = ['is_active']
    def validate(self, attrs):
        if set(self.initial_data.keys()) != {'is_active'}:
            raise serializers.ValidationError("Solo se puede enviar el campo is_active")
        return attrs

class PermissionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = Permissions
        fields = '__all__'
        extra_kwargs = {
            'id_permissions': {'read_only':True}
        }