from api.Inventory.models import Inventory
from openpyxl import Workbook
from django.http import HttpResponse

def create_inventory_for_variant(variant):
    return Inventory.objects.create(
        variant = variant,
        stock = 0
    )

def Export_products_list(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = 'listado de productos'

    headers = [
        'nombre',
        'categoria',
        'precio de venta',
        'precio de compra',
        'estado',
        'talla',
        'color',
        'SKU'
    ]
    ws.append(headers)

    for product  in queryset:
        for variant in product.variants.all():
            ws.append([
                product.name,
                product.category.name,
                product.price,
                product.purchase_price,
                "Activo" if product.is_active == True else "Inactivo",
                variant.size.name,
                variant.color.name,
                variant.sku
            ])
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

    response["Content-Disposition"] = 'attachment; filename="compras.xlsx"'

    wb.save(response)

    return response