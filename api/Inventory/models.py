from django.db import models
from api.Products.models import VariantProduct

class Inventory(models.Model):
    id_inventory = models.AutoField(primary_key=True)
    variant = models.OneToOneField(VariantProduct, on_delete=models.CASCADE)
    stock = models.IntegerField()
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Inventory'
        constraints = [
            models.CheckConstraint(
                condition=models.Q(stock__gte=0),
                name='stock_greater_than_0',
                violation_error_code='invalid_stock',
                violation_error_message='el stock no puede ser menor a 0'
            )
        ]

# Create your models here.
