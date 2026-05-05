from rest_framework import serializers
from .models import Inventory
from django.db import transaction

def add_stock(variant, amount):
    if amount <= 0:
        raise serializers.ValidationError(
            detail='el stock no puede ser negativo',
            code='invalid_stock'
        )
    try:
        with transaction.atomic():
            inventory = Inventory.objects.select_for_update().get(variant=variant)
            inventory.stock += amount
            inventory.save()
        return inventory
    except Inventory.DoesNotExist:
        raise serializers.ValidationError(
            detail='esta variante no existe',
            code='Not_found'
        )
    
def out_stock(variant, amount):
    if amount <= 0:
        raise serializers.ValidationError(
            detail='la cantidad a descontar no puede ser menor a 0',
            code='invalid_stock'
        )
    try:
        with transaction.atomic():
            inventory = Inventory.objects.select_for_update().get(variant=variant)
            if inventory.stock < amount:
                raise serializers.ValidationError(
                    detail='no hay suficiente stock para esta venta',
                    code='insufficient_stock'
                )
            inventory.stock -= amount
            inventory.save()
        return inventory
    except Inventory.DoesNotExist:
        raise serializers.ValidationError(
            detail='esta variante no existe',
            code='not_found'
        )
    


    