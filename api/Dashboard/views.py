from django.shortcuts import render
from rest_framework import viewsets, status, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
import logging
from api.Sales.models import Sales, SalesDetail
from api.Sales.serializers import SalesDetailsSerializer, SalesSerializer
from api.Orders.models import Orders, OrdersDetail
from api.Orders.serializers import OrderDetailSerializer, OrdersSerializers
from api.Users.models import Users
from api.Users.serializers import UsersSerializer
from api.Sales.models import Sales, SalesDetail
from api.Sales.serializers import SalesSerializer, SalesDetailsSerializer
from api.Returns.models import Returns
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import datetime

logger = logging.getLogger(__name__)


class DashboardViewSets(viewsets.GenericViewSet):

    @action(detail=False,methods=['GET'])
    def get_users_active(self, request):
        try:
            active = True

            users_active = Users.objects.filter(is_active=active).count()
            # serializer = UsersSerializer(users_active, many=True)
            return Response({'results':users_active, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def get_pending_orders(self, request):
        try:
            orders = Orders.objects.filter(state__name_state="Pendiente").count()
            # serializer = OrdersSerializers(orders, many=True)
            return Response({'results':orders, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'])
    def cantidad_ventas_mes(self, request):
        try:
            # Obtener fecha desde hace 30 días
            hace_30_dias = timezone.now() - timezone.timedelta(days=30)
            
            cantidad = Sales.objects.filter(date_sale__gte=hace_30_dias).count()
            
            return Response({'success': True,'results': cantidad}, status=status.HTTP_200_OK)
            
        except Exception as ex:
            return Response({'success': False,'error': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def dinero_ventas_mes(self, request):
        try:
            # Obtener fecha desde hace 30 días
            hace_30_dias = timezone.now() - timezone.timedelta(days=30)
            
            resultado = Sales.objects.filter(date_sale__gte=hace_30_dias).aggregate(total_dinero=Sum('total'))
            
            total = resultado['total_dinero'] or 0
            
            return Response({'success': True,'results': float(total)}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'success': False,'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'])
    def productos_mas_vendidos(self, request):
        try:
            top_productos = SalesDetail.objects.values('variant__product__name')\
                .annotate(total_vendido=Sum('quantity'))\
                .order_by('-total_vendido')[:5]
            
            resultados = [
                {
                    'producto': item['variant__product__name'],
                    'cantidad': item['total_vendido']
                } for item in top_productos
            ]
            
            print(resultados)
            return Response({'success': True, 'results': resultados}, status=status.HTTP_200_OK)
            
        except Exception as ex:
            print(ex)
            return Response({'success': False, 'error': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'])
    def distribucion_categorias(self, request):
        try:
            # Calcular total general desde SalesDetail
            total_general = SalesDetail.objects.aggregate(total_todo=Sum('subtotal'))['total_todo'] or 0
            
            if total_general == 0:
                return Response({'success': True, 'results': []}, status=status.HTTP_200_OK)

            categorias_data = SalesDetail.objects.values('variant__product__category__name')\
                .annotate(total_categoria=Sum('subtotal'))\
                .order_by('-total_categoria')

            resultados = []
            for item in categorias_data:
                total_cat = item['total_categoria'] or 0
                porcentaje = (total_cat * 100) / total_general
                
                resultados.append({
                    'categoria': item['variant__product__category__name'],
                    'total_vendido': float(total_cat),
                    'porcentaje': round(float(porcentaje), 2)
                })
            print(resultados)

            return Response({'success': True, 'results': resultados}, status=status.HTTP_200_OK)
            
        except Exception as ex:
            print(ex)
            return Response({'success': False, 'error': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_metrics(self, request):
        try:
            cantidad_devoluciones = Returns.objects.count()
            logger.info(f'métricas de devoluciones obtenidas')
            return Response({
                'message': 'métricas de devoluciones',
                'metrics': {
                    'cantidad_devoluciones': cantidad_devoluciones
                },
                'success': True
            }, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error al obtener métricas: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def dinero_ventas_por_mes(self, request):
        try:
            now = timezone.now()
            resultados = []
            meses_nombres = {
                1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
            }
            
            for i in range(5, -1, -1):
                year = now.year
                month = now.month - i
                while month <= 0:
                    month += 12
                    year -= 1
                
                suma = Sales.objects.filter(
                    date_sale__month=month,
                    date_sale__year=year
                ).aggregate(total_dinero=Sum('total'))['total_dinero'] or 0
                
                resultados.append({
                    'mes': meses_nombres[month],
                    'valor': float(suma)
                })
                
            return Response({'success': True, 'results': resultados}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def cantidad_ventas_por_mes(self, request):
        try:
            now = timezone.now()
            resultados = []
            meses_nombres = {
                1: 'Ene', 2: 'Feb', 3: 'Mar', 4: 'Abr', 5: 'May', 6: 'Jun',
                7: 'Jul', 8: 'Ago', 9: 'Sep', 10: 'Oct', 11: 'Nov', 12: 'Dic'
            }
            
            for i in range(5, -1, -1):
                year = now.year
                month = now.month - i
                while month <= 0:
                    month += 12
                    year -= 1
                
                cantidad = Sales.objects.filter(
                    date_sale__month=month,
                    date_sale__year=year
                ).count()
                
                resultados.append({
                    'mes': meses_nombres[month],
                    'valor': cantidad
                })
                
            return Response({'success': True, 'results': resultados}, status=status.HTTP_200_OK)
        except Exception as e:
            return Response({'success': False, 'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Create your views here.
