from openpyxl import Workbook
from django.http import HttpResponse

def Export_returns_list(queryset):
    wb = Workbook()
    ws = wb.active

    ws.title = "Listado de devoluciones" 

    headers = [
        
    ]
