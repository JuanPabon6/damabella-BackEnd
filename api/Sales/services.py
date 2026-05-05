from openpyxl import Workbook
from django.http import HttpResponse

def Export_sales_list(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = 'Lista de ventas'

    headers = [
        'numero de compra',
        'cliente',
        'fecha de venta',
        'estado',
        'metodo de pago',
        'subtotal',
        'iva',
        'total',
        'producto'
    ]

    ws.append(headers)

    for sale in queryset:
        for detail in sale.sale_detail.all():
            ws.append([
                sale.number_sale,
                sale.client.name,
                sale.date_sale,
                sale.state.name_state,
                sale.payment_method.name,
                sale.subtotal,
                sale.iva,
                sale.total,
                f'{detail.variant.product.name} - {detail.variant.sku}',
                detail.quantity
            ])
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="ventas.xlsx"'

    wb.save(response)
    return response


