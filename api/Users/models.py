from django.db import models
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager
from api.Roles.models import Roles
from django.utils import timezone
from datetime import timedelta
import random

class UserManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user  = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

class Users(AbstractBaseUser):
    id_user = models.AutoField(primary_key=True)
    type_doc = models.ForeignKey('Typesdoc', on_delete=models.PROTECT)
    doc_identity = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=100)
    email = models.EmailField(max_length=120, unique=True)
    # password = models.TextField()
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=200, default="sin direccion") 
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    id_rol = models.ForeignKey(Roles, on_delete=models.PROTECT, default=2)
    is_active = models.BooleanField(default=True)

    objects = UserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['name']

    class Meta:
        db_table = 'Users'

class PasswordResetOTP(models.Model):
    user       = models.ForeignKey(Users, on_delete=models.CASCADE)
    code       = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    is_used    = models.BooleanField(default=False)

    def is_valid(self):
        expiration = self.created_at + timedelta(minutes=10)
        return not self.is_used and timezone.now() < expiration

    class Meta:
        db_table = 'PasswordResetOTP'

class Typesdoc(models.Model):
    id_doc = models.AutoField(primary_key=True)
    name = models.CharField(max_length=40, unique=True)

    class Meta:
        db_table = 'Types_docs'
# Create your models here.
