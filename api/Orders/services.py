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
    ws.append(headers)

    for order in queryset:
        client_name = order.client.name if order.client else 'Sin Cliente'
        payment_name = order.payment_method.name if order.payment_method else 'Sin Método'
        state_name = order.state.name_state if order.state else 'Sin Estado'
        
        # Formatear la fecha como string sin información de zona horaria para evitar que openpyxl falle
        order_date_str = order.order_date.strftime('%Y-%m-%d %H:%M:%S') if order.order_date else ''
        
        details = order.detail_order.all()
        if not details.exists():
            ws.append([
                order.number_order,
                client_name,
                order_date_str,
                payment_name,
                order.address_shipment or '',
                order.person_receives or '',
                order.subtotal or 0,
                order.iva or 0,
                order.total or 0,
                order.observations or '',
                state_name,
                'Sin productos',
                0
            ])
        else:
            for detail in details:
                product_str = 'Producto no especificado'
                if detail.variant:
                    sku_str = detail.variant.sku or 'Sin SKU'
                    prod_name = detail.variant.product.name if detail.variant.product else 'Producto sin nombre'
                    product_str = f'{prod_name} - {sku_str}'
                
                ws.append([
                    order.number_order,
                    client_name,
                    order_date_str,
                    payment_name,
                    order.address_shipment or '',
                    order.person_receives or '',
                    order.subtotal or 0,
                    order.iva or 0,
                    order.total or 0,
                    order.observations or '',
                    state_name,
                    product_str,
                    detail.quantity or 0
                ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="pedidos.xlsx"'

    wb.save(response)
    return response
    