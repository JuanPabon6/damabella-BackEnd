from openpyxl import Workbook
from django.http import HttpResponse

def Export_users_list(queryset):
    wb = Workbook()
    ws = wb.active
    ws.title = "Lista de usuarios"

    headers = [
        "Documento",
        "Nombre",
        "Email",
        "Teléfono",
        "Dirección",
        "Rol",
        "Activo"
    ]
    ws.append(headers)

    for user in queryset:
        ws.append([
            user.doc_identity,
            user.name,
            user.email,
            user.phone,
            user.address,
            user.id_rol.name if user.id_rol else "",
            user.is_active
        ])

    response = HttpResponse(
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )
    response["Content-Disposition"] = 'attachment; filename="usuarios.xlsx"'

    wb.save(response)
    return response
