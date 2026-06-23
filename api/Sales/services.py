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
        'producto',
        'cantidad'
    ]

    ws.append(headers)

    for sale in queryset:
        client_name = sale.client.name if sale.client else 'Sin Cliente'
        state_name = sale.state.name_state if sale.state else 'Sin Estado'
        payment_name = sale.payment_method.name if sale.payment_method else 'Sin Método'
        date_sale_str = sale.date_sale.strftime('%Y-%m-%d %H:%M:%S') if sale.date_sale else ''

        details = sale.sale_detail.all()
        if not details.exists():
            ws.append([
                sale.number_sale,
                client_name,
                date_sale_str,
                state_name,
                payment_name,
                sale.subtotal or 0,
                sale.iva or 0,
                sale.total or 0,
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
                    sale.number_sale,
                    client_name,
                    date_sale_str,
                    state_name,
                    payment_name,
                    sale.subtotal or 0,
                    sale.iva or 0,
                    sale.total or 0,
                    product_str,
                    detail.quantity or 0
                ])
                
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="ventas.xlsx"'

    wb.save(response)
    return response


