from rest_framework import serializers
from .models import Roles, Permissions, RolPermission

class RolesSerializers(serializers.ModelSerializer):
    permissions = serializers.PrimaryKeyRelatedField(
        queryset = Permissions.objects.all(),
        many=True,
        write_only=True,
        required=False
    )

    def validate_permissions(self, value):
        if not value or value == 0:
            return []
        return value

    def create(self, validated_data):
        permissions = validated_data.pop('permissions', None)
        rol = Roles.objects.create(**validated_data)

        if rol.name.lower() == 'administrador':
            for perm in Permissions.objects.all():
                RolPermission.objects.get_or_create(rol=rol, permission=perm)

        elif permissions:
            for perm in permissions:
                RolPermission.objects.get_or_create(rol=rol, permission=perm)
        else:
            DEFAULT_PERMISSIONS =[
                ('Products','View'),
                ('Categories', 'View'),
                ('Users', 'View'),
            ]
            for module, action in DEFAULT_PERMISSIONS:
                try:
                    perm = Permissions.objects.get(
                        Module_permission=module,
                        Action=action
                    )
                    RolPermission.objects.get_or_create(rol=rol, permission=perm)
                except Permissions.DoesNotExist:
                    pass
        return rol

    class Meta:
        model = Roles
        fields = '__all__'
        extra_kwargs = {
            'idRol': {'read_only':True},
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

class RolPermissionSerializer(serializers.ModelSerializer):
    def validate(self, attrs):
        rol = attrs.get('rol')
        permission = attrs.get('permission')
        if RolPermission.objects.filter(rol=rol, permission=permission).exists():
            raise serializers.ValidationError(
                'este permiso ya esta asignado al rol'
            )
        return attrs

    class Meta:
        model = RolPermission
        fields = '__all__'