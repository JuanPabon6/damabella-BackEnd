from django.db import models

class Roles(models.Model):
    idRol = models.AutoField(primary_key=True)
    name = models.CharField(max_length=20)
    description = models.TextField(null=True, blank=True)

    class Meta:
        db_table = 'Roles'
    
# Create your models here.
