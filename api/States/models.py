from django.db import models

class States(models.Model):
    id_state = models.AutoField(primary_key=True)
    name_state = models.CharField(max_length=30, unique=True)

    class Meta:
        db_table = 'States'

# Create your models here.
