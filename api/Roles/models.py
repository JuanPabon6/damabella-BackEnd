from django.db import models

class Roles(models.Model):
    idRol = models.AutoField(primary_key=True)
    name = models.CharField(max_length=50, unique=True)
    description = models.CharField(max_length=200, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    permissions = models.ManyToManyField('Permissions',through='RolPermission',related_name='roles')

    class Meta:
        db_table = 'Roles'

class Permissions(models.Model):
    id_permissions = models.AutoField(primary_key=True)
    Module_permission = models.CharField(max_length=50)
    Action = models.CharField(max_length=50)

    class Meta:
        db_table = 'Permissions'

class RolPermission(models.Model):
    rol = models.ForeignKey(Roles, on_delete=models.CASCADE)
    permission = models.ForeignKey(Permissions, on_delete=models.CASCADE)

    class Meta:
        db_table = 'Rol_permission'
        unique_together = ('rol','permission')
    
# Create your models here.
