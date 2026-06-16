from django.conf import settings
from django.db import models
from api.Users.models import Clients
from api.States.models import States
from api.Products.models import VariantProduct
import random,string

def generate_number_order():
    while True:
        number = "PED-"+"".join(random.choices(string.digits, k=8))
        if not Orders.objects.filter(number_order=number).exists():
            return number

class PaymentMethods(models.Model):
    id_method = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table  = 'Payment_Methods'

class Orders(models.Model):
    id_order = models.AutoField(primary_key=True)
    number_order = models.CharField(max_length=50, unique=True, editable=False, default=generate_number_order)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, default=1)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='orders', db_column='user_id')
    order_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.ForeignKey(PaymentMethods, on_delete=models.PROTECT)
    address_shipment = models.CharField(max_length=200)
    person_receives = models.CharField(max_length=100)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    iva = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    total = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    observations = models.CharField(max_length=300, null=True, blank=True)
    state = models.ForeignKey(States, on_delete=models.PROTECT)

    class Meta:
        db_table = 'Orders'


class OrdersDetail(models.Model):
    id_detail = models.AutoField(primary_key=True)
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='detail_order')
    variant = models.ForeignKey(VariantProduct, on_delete=models.PROTECT, related_name='details_order')
    quantity = models.IntegerField()
    sales_price = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    class Meta:
        db_table='Orders_detail'
        constraints = [
            models.CheckConstraint(
                name='quantity_greather_than',
                condition=models.Q(quantity__gt=0),
                violation_error_code='quantity_invalid',
                violation_error_message='la cantidad no puede ser menor o igual a 0'
            )
        ]


# Create your models here.
