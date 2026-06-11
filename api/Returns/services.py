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
        for detail in return_obj.return_detail.all():
            ws.append([
                return_obj.return_number,
                return_obj.sale.number_sale,
                return_obj.return_date,
                return_obj.reason,
                return_obj.state.name_state,
                f'{detail.variant.product.name} - {detail.variant.sku}',
                detail.quantity,
                detail.subtotal,
                return_obj.total,
                return_obj.balance_in_favor,
                return_obj.difference_to_pay
            ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="devoluciones.xlsx"'

    wb.save(response)
    return response

