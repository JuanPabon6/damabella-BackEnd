# Generated manually to fix state values after converting ForeignKey to BooleanField
from django.db import migrations

def fix_sales_state(apps, schema_editor):
    Sales = apps.get_model('Sales', 'Sales')
    # Set state = False for all sales that do not have a void_reason (null or empty)
    # since the database migration converted the old ForeignKey integer IDs to Boolean True.
    Sales.objects.filter(void_reason__isnull=True).update(state=False)
    Sales.objects.filter(void_reason='').update(state=False)

class Migration(migrations.Migration):

    dependencies = [
        ('Sales', '0007_alter_sales_state'),
    ]

    operations = [
        migrations.RunPython(fix_sales_state),
    ]
