from django.db import models

class Categories(models.Model):
    id_category = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100, unique=True)
    description = models.CharField(max_length=200, blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'Categories'
# Create your models here.
