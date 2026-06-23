from openpyxl import Workbook
from django.http import HttpResponse

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
        provider_name = purchase.provider.name if purchase.provider else 'Sin Proveedor'
        state_name = purchase.state.name_state if purchase.state else 'Sin Estado'
        purchase_date_str = purchase.purchase_date.strftime('%Y-%m-%d %H:%M:%S') if purchase.purchase_date else ''

        details = purchase.detail_purchase.all()
        if not details.exists():
            ws.append([
                purchase.purchase_number,
                provider_name,
                state_name,
                'Sin productos',
                0,
                0,
                purchase.subtotal or 0,
                purchase.iva or 0,
                purchase.total or 0,
                purchase_date_str,
                purchase.observations or ''
            ])
        else:
            for detail in details:
                product_str = 'Producto no especificado'
                if detail.variant:
                    sku_str = detail.variant.sku or 'Sin SKU'
                    prod_name = detail.variant.product.name if detail.variant.product else 'Producto sin nombre'
                    product_str = f'{prod_name} - {sku_str}'
                
                ws.append([
                    purchase.purchase_number,
                    provider_name,
                    state_name,
                    product_str,
                    detail.purchase_price or 0,
                    detail.quantity or 0,
                    purchase.subtotal or 0,
                    purchase.iva or 0,
                    purchase.total or 0,
                    purchase_date_str,
                    purchase.observations or ''
                ])
                
    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="compras.xlsx"'

    wb.save(response)
    return response
