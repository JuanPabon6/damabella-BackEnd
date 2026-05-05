from openpyxl import Workbook
from django.http import HttpResponse

def Export_orders_list(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = 'listado de pedidos'

    headers = [
        'numero de orden',
        'cliente',
        'fecha del pedido',
        'metodo de pago',
        'direccion de domicilio',
        'persona que recibe',
        'subtotal',
        'iva',
        'total',
        'observaciones',
        'estado', 
        'producto',
        'cantidad'
    ]

    for order in queryset:
        for detail in order.detail_order.all():
            ws.append([
                order.number_order,
                order.client.name,
                order.order_date,
                order.payment_method.name,
                order.address_shipment,
                order.person_receives,
                order.subtotal,
                order.iva,
                order.total,
                order.observations,
                order.state.name_state,
                f'{detail.variant.product.name}- {detail.variant.sku}',
                detail.quantity
            ])
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="compras.xlsx"'

    wb.save(response)
    return response
    