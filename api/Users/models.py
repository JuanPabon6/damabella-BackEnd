from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from api.Roles.models import Roles

class Users(models.Model):
    id_user = models.AutoField(primary_key=True)
    type_doc = models.ForeignKey('Typesdoc', on_delete=models.PROTECT)
    doc_identity = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=120, unique=True)
    password = models.TextField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=200, default="sin direccion") 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id_rol = models.ForeignKey(Roles, on_delete=models.PROTECT, default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'Users'

class Typesdoc(models.Model):
    id_doc = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = 'Types_docs'
# Create your models here.
