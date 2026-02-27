from django.db import models
from api.Users.models import Typesdoc

class Providers(models.Model):
    id_provider = models.AutoField(primary_key=True)
    name = models.CharField(max_length=120)
    type_doc =  models.ForeignKey(Typesdoc, on_delete=models.PROTECT)
    number_doc = models.CharField(max_length=30, unique=True)
    contact_name = models.CharField(max_length=100)
    phone = models.CharField(max_length=20) 
    address = models.CharField(max_length=200)
    email = models.EmailField(max_length=120)
    is_active = models.BooleanField(default=True)
    published = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'Providers'
    
# Create your models here.
