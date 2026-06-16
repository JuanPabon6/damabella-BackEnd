from django.conf import settings
from django.db import models
import string, random
from api.Users.models import Clients
from api.States.models import States
from api.Orders.models import PaymentMethods
from api.Products.models import VariantProduct
from api.Orders.models import Orders

def generate_number():
    while True:
        number = 'VEN-'+''.join(random.choices(string.digits, k=8))
        if not Sales.objects.filter(number_sale=number).exists():
            return number

class Sales(models.Model):
    id_sale = models.AutoField(primary_key=True)
    number_sale = models.CharField(max_length=50, unique=True, editable=False, default=generate_number)
    client = models.ForeignKey(Clients, on_delete=models.CASCADE, related_name='sales', default=0)
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, null=True, blank=True, related_name='sales', db_column='user_id')
    order = models.ForeignKey(Orders, on_delete=models.CASCADE, related_name='order_sale', default=None, null=True, blank=True)
    date_sale = models.DateTimeField(auto_now_add=True)
    state = models.ForeignKey(States, on_delete=models.PROTECT, related_name='sales')
    payment_method = models.ForeignKey(PaymentMethods, on_delete=models.PROTECT, related_name='sales')
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    iva = models.DecimalField(max_digits=10, decimal_places=2)
    total = models.DecimalField(max_digits=10, decimal_places=2)
    output_executing = models.BooleanField(default=False)
    return_executing = models.BooleanField(default=False)
    void = models.BooleanField(default=False)
    void_reason = models.CharField(max_length=200, blank=True, null=True)

    class Meta:
        db_table = 'Sales'

class SalesDetail(models.Model):
    id_detail = models.AutoField(primary_key=True)
    sale = models.ForeignKey(Sales, on_delete=models.CASCADE, related_name='sale_detail')
    variant = models.ForeignKey(VariantProduct, on_delete=models.CASCADE, related_name='sales_details')
    quantity = models.IntegerField()
    unit_price = models.DecimalField(max_digits=10,decimal_places=2)
    subtotal = models.DecimalField(max_digits=10, decimal_places=2)
    creation_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'SalesDetail'
        constraints = [
            models.CheckConstraint(
                name='quantity_gt_cero',
                condition=models.Q(quantity__gt=0),
                violation_error_code='quantity invalid',
                violation_error_message='la cantidad no puede ser menor o 0'
            )
        ]




# Create your models here.
