from openpyxl import Workbook
from django .http import HttpResponse

def Export_purchases_list(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Lista de compras"

    headers = [
        'numero de compra',
        'proveedor',
        'estado',
        'productos',
        'precio de compra',
        'cantodad',
        'subtotal',
        'iva',
        'total',
        'fecha de compra',
        'observaciones'
    ]
    ws.append(headers)

    for purchase in queryset:
        for detail in purchase.detail_purchase.all():
            ws.append([
                purchase.purchase_number,
                purchase.provider.name,
                purchase.state.name_state,
                f'{detail.variant.product.name} - {detail.variant.sku}',
                detail.purchase_price,
                detail.quantity,
                purchase.subtotal,
                purchase.iva,
                purchase.total,  
                purchase.purchase_date,
                purchase.observations          
            ])
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="compras.xlsx"'

    wb.save(response)
    return response
