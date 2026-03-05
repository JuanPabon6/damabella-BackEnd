from rest_framework import serializers
from .models import Clients

class ClientsSerializers(serializers.ModelSerializer):
    class Meta:
        model = Clients
        fields = '__all__'
        extra_kwargs = {
            'id_client':{'read_only':True}
        }

class StateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clients
        fields = ['state']