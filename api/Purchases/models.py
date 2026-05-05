from django.db import models
from api.Providers.models import Providers
from api.States.models import States
from api.Products.models import VariantProduct
import random, string

def generar_numero_compra():
    while True:
        number = 'ORD-'+''.join(random.choices(string.digits, k=8))
        if not Purchases.objects.filter(purchase_number=number).exists():
            return number

class Purchases(models.Model):
    id_purchase = models.AutoField(primary_key=True)
    purchase_number = models.CharField(max_length=50, unique=True, editable=False, default=generar_numero_compra)
    provider = models.ForeignKey(Providers, on_delete=models.PROTECT, related_name='purchases')
    state = models.ForeignKey(States, on_delete=models.PROTECT, related_name='purchases')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    purchase_date = models.DateTimeField(auto_now_add=True)
    registration_date = models.DateField(auto_now=True)
    observations = models.CharField(max_length=300, blank=True, null=True)
    image = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'Purchases'

class PurchaseDetail(models.Model):
    id_detail = models.AutoField(primary_key=True)
    purchase = models.ForeignKey(Purchases, on_delete=models.CASCADE, related_name='detail_purchase')
    variant = models.ForeignKey(VariantProduct, on_delete=models.PROTECT, related_name='purchases_details')
    quantity = models.IntegerField()
    purchase_price = models.DecimalField(max_digits=10, decimal_places=2)
    sales_price = models.DecimalField(max_digits=10, decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    class Meta:
        db_table = 'Purchase_detail'
        constraints = [
            models.CheckConstraint(
                name='quantity_gt_0',
                condition=models.Q(quantity__gt=0),
                violation_error_code='quantity_invalid',
                violation_error_message='la cantidad no puede ser menor o igual a 0'
            )
        ]



# Create your models
