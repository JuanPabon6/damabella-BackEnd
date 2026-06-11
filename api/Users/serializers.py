from rest_framework import serializers
from .models import Users, Typesdoc, PasswordResetOTP
from rest_framework_simplejwt.tokens import RefreshToken
from api.Roles.models import RolPermission
from django.core.mail import send_mail
from django.conf import settings
import random
from .models import Clients
from django.db import transaction
from api.Roles.models import Roles

class ChangePasswordSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password     = serializers.CharField(write_only=True)

    def validate(self, attrs):
        user = self.context['request'].user
        if not user.check_password(attrs['current_password']):
            raise serializers.ValidationError(
                {'message': 'La contraseña actual es incorrecta', 'success': False}
            )
        return attrs

    def save(self):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save()


class RequestOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        try:
            self.user = Users.objects.get(email=value)
        except Users.DoesNotExist:
            raise serializers.ValidationError('No existe un usuario con este email')
        return value

    def save(self):
        # Invalidar OTPs anteriores
        PasswordResetOTP.objects.filter(
            user=self.user,
            is_used=False
        ).update(is_used=True)

        # Generar código de 6 dígitos
        code = str(random.randint(100000, 999999))

        PasswordResetOTP.objects.create(user=self.user, code=code)

        # Enviar email
        send_mail(
            subject='Código de recuperación - Damabella',
            message=f'Tu código de recuperación es: {code}\nExpira en 10 minutos.',
            from_email=settings.EMAIL_HOST_USER,
            recipient_list=[self.user.email],
            fail_silently=False,
        )
        return code


class ValidateOTPSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code  = serializers.CharField(max_length=6)

    def validate(self, attrs):
        try:
            user = Users.objects.get(email=attrs['email'])
        except Users.DoesNotExist:
            raise serializers.ValidationError('No existe un usuario con este email')

        try:
            otp = PasswordResetOTP.objects.filter(
                user=user,
                code=attrs['code'],
                is_used=False
            ).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            raise serializers.ValidationError('Código inválido')

        if not otp.is_valid():
            raise serializers.ValidationError('El código ha expirado')

        return attrs

    def save(self):
        # ← ya no marca como usado, solo valida
        pass


class ResetPasswordSerializer(serializers.Serializer):
    email        = serializers.EmailField()
    code         = serializers.CharField(max_length=6)
    new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        try:
            user = Users.objects.get(email=attrs['email'])
        except Users.DoesNotExist:
            raise serializers.ValidationError('No existe un usuario con este email')

        try:
            otp = PasswordResetOTP.objects.filter(
                user=user,
                code=attrs['code'],
                is_used=False
            ).latest('created_at')
        except PasswordResetOTP.DoesNotExist:
            raise serializers.ValidationError('Código inválido')

        if not otp.is_valid():
            raise serializers.ValidationError('El código ha expirado')

        self.user = user
        self.otp  = otp
        return attrs

    def save(self):
        self.user.set_password(self.validated_data['new_password'])
        self.user.save()
        self.otp.is_used = True
        self.otp.save()
    

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        try:
            user = Users.objects.get(email=email)
        except Users.DoesNotExist:
            raise serializers.ValidationError(
                {'success':False, 'message':'credenciales invalidas'}
            )
        if not user.check_password(password):
            raise serializers.ValidationError(
                {'success':False, 'message':'credenciales invalidas'}
            )
        if not user.is_active:
            raise serializers.ValidationError(
                {'success':False, 'message':'este usuario no esta activo'}
            )
        
        rol_permission = RolPermission.objects.filter(
            rol=user.id_rol
        ).select_related('permission')

        permissionsDict = {}

        for rp in rol_permission:
            module = rp.permission.Module_permission
            action = rp.permission.Action
            if module not in permissionsDict:
                permissionsDict[module] = []
            permissionsDict[module].append(action)

        refresh = RefreshToken.for_user(user=user)
        refresh['name'] = user.name
        refresh['email'] = user.email
        refresh['rol'] = user.id_rol_id
        refresh['rol_name'] = user.id_rol.name
        refresh['permissions'] = permissionsDict

        return {
            'success': True,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user': {
                'id':          user.id_user,
                'name':        user.name,
                'email':       user.email,
                'rol':         user.id_rol_id,
                'rol_name':    user.id_rol.name,
                'permissions': permissionsDict,
            }
        }

class UsersSerializer(serializers.ModelSerializer):
    role_name = serializers.CharField(source='id_rol.name', read_only=True)
    type_doc_name = serializers.CharField(source='type_doc.name', read_only=True)
    class Meta:
        model = Users
        fields = '__all__'
        extra_kwargs = {
            'created_at':{'read_only':True},
            'updated_at':{'read_only':True},
            'password':{'write_only':True},
        }
    def create(self, validated_data):
        password = validated_data.pop('password')
        user     = Users(**validated_data)
        user.set_password(password)
        user.save()
        return user

    def update(self, instance, validated_data):
        password = validated_data.pop('password', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        if password:
            instance.set_password(password)
        instance.save()
        return instance


class UsersPatchActiveSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = ['is_active']

    def validate(self, attrs):
        if set(self.initial_data.keys()) != {'is_active'}:
            raise serializers.ValidationError("Solo se puede enviar el campo is_active")
        return attrs
    
class TypesDocsSerializers(serializers.ModelSerializer):
    class Meta:
        model = Typesdoc
        fields = '__all__'
        extra_kwargs = {
            'id_doc':{'read_only':True}
        }

class ClientsSerializers(serializers.ModelSerializer):
    # users = UsersSerializer(many=True, source='users_client')
    class Meta:
        model = Clients
        fields = '__all__'
        extra_kwargs = {
            'id_client':{'read_only':True}
        }

class ClientsUnifiedSerializer(serializers.ModelSerializer):
    # Campos virtuales write_only que el formulario del front enviará para crear el User
    email = serializers.EmailField(write_only=True)
    password = serializers.CharField(write_only=True, required=False, default="123456")
    doc_identity = serializers.CharField(write_only=True)
    
    class Meta:
        model = Clients
        fields = [
            # 'id_client', 'name', 'type_doc', 'doc', 'phone', 
            # 'address', 'email', 'state', 'city', 
            # 'password', 'doc_identity'
            '__all__'
        ]
        extra_kwargs = {
            'id_client': {'read_only': True},
            'user':{'read_only':True}
        }

    def create(self, validated_data):
        # Extraemos la data exclusiva de la tabla de Usuarios
        email = validated_data.pop('email')
        password = validated_data.pop('password')
        doc_identity = validated_data.pop('doc_identity')
        
        # Mantenemos los datos comunes o propios de Clientes
        name = validated_data.get('name')
        phone = validated_data.get('phone')
        address = validated_data.get('address')
        type_doc_instance = validated_data.get('type_doc')

        # Bloque atómico: si algo falla aquí adentro, se cancela todo en cascada
        with transaction.atomic():
            # Buscamos de forma segura el rol 'cliente' en el sistema
            try:
                rol_cliente = Roles.objects.get(name__icontains='cliente')
            except Roles.DoesNotExist:
                # Si por alguna razón cambiaron los nombres en BD, usamos el ID por defecto para clientes (ej: 2)
                rol_cliente = Roles.objects.get(id=2) 

            # Creamos la instancia en la tabla de Usuarios usando la lógica de password hashing
            user_instance = Users.objects.create(
                email=email,
                name=name,
                type_doc=type_doc_instance,
                doc_identity=doc_identity,
                phone=phone,
                address=address,
                id_rol=rol_cliente
            )
            user_instance.set_password(password)
            user_instance.save()

            # Creamos el Cliente vinculándolo al usuario recién creado y forzando saldo en 0
            client_instance = Clients.objects.create(
                user=user_instance,
                saldo_a_favor=0.00,
                **validated_data
            )

            return client_instance

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clients
        fields = ['state']