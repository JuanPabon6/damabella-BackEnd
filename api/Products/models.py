from django.db import models
from api.Categories.models import Categories

class Products(models.Model):
    id_product = models.AutoField(primary_key=True)
    name = models.CharField(max_length=120)
    category = models.ForeignKey(Categories, on_delete=models.CASCADE, related_name='products', default=1)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'Products'
        constraints =[ models.CheckConstraint(
            condition= models.Q(price__gte=0),
            name='price_greater_than_0',
            violation_error_code= 'precio_negativo',
            violation_error_message= 'el precio del producto no puede ser negativo'
        )
        ]

class Colors(models.Model):
    id_color = models.AutoField(primary_key=True)
    name = models.CharField(max_length=75)

    class Meta:
        db_table = 'Colors'

class Sizes(models.Model):
    id_size = models.AutoField(primary_key=True)
    name = models.CharField(max_length=75)

    class Meta:
        db_table = 'Sizes'

class VariantProduct(models.Model):
    id_variant = models.AutoField(primary_key=True)
    product = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='variants')
    size = models.ForeignKey(Sizes, on_delete=models.PROTECT, related_name='variants')
    color = models.ForeignKey(Colors, on_delete=models.PROTECT, related_name='variants')
    sku = models.CharField(max_length=50, unique=True)

    class Meta:
        db_table = 'Variant_product'
        unique_together = ['product','size', 'color']

class ProductPhoto(models.Model):
    id =models.AutoField(primary_key=True)
    producto = models.ForeignKey(Products, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(upload_to='products/photos/')

    class Meta:
        db_table = 'Product_photo'
# Create your models here.
