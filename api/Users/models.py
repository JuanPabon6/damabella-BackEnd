from django.db import models
from django.contrib.auth.models import AbstractBaseUser
from api.Roles.models import Roles

class Users(models.Model):
    doc_identity = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=40)
    email = models.EmailField(max_length=45, unique=True)
    password = models.TextField()
    phone = models.CharField(max_length=25)
    address = models.CharField(max_length=150, default="sin direccion") 
    id_rol = models.ForeignKey(Roles, on_delete=models.CASCADE, default=1)
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = 'Users'
# Create your models here.
