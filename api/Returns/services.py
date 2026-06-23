from openpyxl import Workbook
from django.http import HttpResponse

def Export_returns_list(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Listado de devoluciones"

    headers = [
        'número de devolución',
        'venta relacionada',
        'fecha de devolución',
        'razón',
        'estado',
        'producto - sku',
        'cantidad',
        'subtotal',
        'total devolución',
        'saldo a favor',
        'diferencia a pagar'
    ]

    ws.append(headers)

    for return_obj in queryset:
        sale_number = return_obj.sale.number_sale if return_obj.sale else 'Sin Venta'
        state_name = 'Anulado' if return_obj.state else 'Activo'
        return_date_str = return_obj.return_date.strftime('%Y-%m-%d %H:%M:%S') if return_obj.return_date else ''

        details = return_obj.return_detail.all()
        if not details.exists():
            ws.append([
                return_obj.return_number,
                sale_number,
                return_date_str,
                return_obj.reason or '',
                state_name,
                'Sin productos',
                0,
                0,
                return_obj.total or 0,
                return_obj.balance_in_favor or 0,
                return_obj.difference_to_pay or 0
            ])
        else:
            for detail in details:
                product_str = 'Producto no especificado'
                if detail.variant:
                    sku_str = detail.variant.sku or 'Sin SKU'
                    prod_name = detail.variant.product.name if detail.variant.product else 'Producto sin nombre'
                    product_str = f'{prod_name} - {sku_str}'
                
                ws.append([
                    return_obj.return_number,
                    sale_number,
                    return_date_str,
                    return_obj.reason or '',
                    state_name,
                    product_str,
                    detail.quantity or 0,
                    detail.subtotal or 0,
                    return_obj.total or 0,
                    return_obj.balance_in_favor or 0,
                    return_obj.difference_to_pay or 0
                ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="devoluciones.xlsx"'

    wb.save(response)
    return response

