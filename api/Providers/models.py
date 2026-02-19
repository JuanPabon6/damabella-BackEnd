from django.db import models

class Providers(models.Model):
    nit_document = models.IntegerField(primary_key=True)
    kompany_name = models.CharField(max_length=30)
    contact_name = models.CharField(max_length=35)
    phone = models.CharField(max_length=125) 
    address = models.CharField(max_length=75)

    class Meta:
        db_table = 'Providers'
    
# Create your models here.
