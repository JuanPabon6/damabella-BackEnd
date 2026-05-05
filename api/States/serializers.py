from rest_framework import serializers
from .models import States

class StatesSerializers(serializers.ModelSerializer):
    class Meta:
        model = States
        fields = '__all__'
        extra_kwargs = {
            'id_state' : {'read_only':True}
        }