from rest_framework import serializers
from .models import Users, Typesdoc

class UsersSerializer(serializers.ModelSerializer):
    class Meta:
        model = Users
        fields = '__all__'
        extra_kwargs = {
            'created_at':{'read_only':True},
            'updated_at':{'read_only':True},
            'password':{'write_only':True},
        }
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