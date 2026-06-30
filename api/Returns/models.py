from django.db import models
import random
import string
from api.Sales.models import Sales
from api.States.models import States
from api.Products.models import VariantProduct

def generar_numero_devolucion():
    while True:
        number = 'DEV-'+''.join(random.choices(string.digits, k=8))
        if not Returns.objects.filter(return_number=number).exists():
            return number
        
class Returns(models.Model):
    id_return = models.AutoField(primary_key=True)
    return_number = models.CharField(max_length=50, unique=True, editable=False, default=generar_numero_devolucion)
    sale = models.ForeignKey(Sales, on_delete= models.PROTECT, related_name='return_sale', default=0)
    return_date = models.DateField(auto_now=True)
    reason = models.CharField(max_length=200)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    state = models.BooleanField(default=False)
    observations = models.CharField(max_length=300, null=True, blank=True)
    balance_in_favor = models.DecimalField(max_digits=10, decimal_places=2)
    difference_to_pay = models.DecimalField(max_digits=10,decimal_places=2)

    class Meta:
        db_table = 'Returns'

class ReturnDetail(models.Model):
    id_detail = models.AutoField(primary_key=True)
    return_id = models.ForeignKey(Returns, on_delete=models.CASCADE, related_name='return_detail', default=0)
    variant = models.ForeignKey(VariantProduct, models.PROTECT, related_name='return_details', default=0)
    quantity = models.IntegerField()
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        db_table = 'ReturnsDetail'
        constraints = [
            models.CheckConstraint(
                name='quantity_greate_than_zero',
                condition=models.Q(quantity__gt=0),
                violation_error_code='cantidad_invalida',
                violation_error_message='la cantidad tiene que ser mayor a 0'
            )
        ]

def generar_numero_cambio():
    while True:
        number = 'CAM-'+''.join(random.choices(string.digits, k=8))
        if not Changes.objects.filter(change_number=number).exists():
            return number
        
class Changes(models.Model):
    id_change = models.AutoField(primary_key=True)
    change_number = models.CharField(max_length=50, unique=True , editable=True, default=generar_numero_cambio)
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name='sale')
    reason_of_change = models.CharField(max_length=200)
    state = models.ForeignKey(States, on_delete=models.PROTECT, related_name='change_state')
    stock_applied = models.BooleanField(default=False)
    return_applied = models.BooleanField(default=False)

    class Meta:
        db_table = 'Changes'

class ChangesDetails(models.Model):
    id = models.AutoField(primary_key=True)
    change = models.ForeignKey(Changes, on_delete=models.CASCADE, related_name='change_detail')
    variant_returned = models.ForeignKey(VariantProduct, on_delete=models.PROTECT, related_name='variant_recieved')
    variant_delivered = models.ForeignKey(VariantProduct, on_delete=models.PROTECT, related_name='returned_variant')

    class Meta:
        db_table = 'ChangesDetail'




# Create your models here.
