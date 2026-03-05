from django.db import models
from api.Users.models import Typesdoc, Users

class Clients(models.Model):
    id_client = models.AutoField(primary_key=True)
    name = models.CharField(max_length=100)
    type_doc = models.ForeignKey(Typesdoc, on_delete=models.PROTECT)
    doc = models.CharField(max_length=30, unique=True)
    phone = models.CharField(max_length=20)
    address = models.CharField(max_length=200)
    email = models.EmailField(max_length=120)
    state = models.BooleanField(default=True)
    city = models.CharField(max_length=100)
    # user = models.ForeignKey(Users, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Clients'

# Create your models here.
