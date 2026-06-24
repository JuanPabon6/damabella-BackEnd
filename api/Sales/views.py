from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Sales, SalesDetail
from .serializers import SalesSerializer, SalesDetailsSerializer
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from api.Inventory.services import add_stock
from .services import Export_sales_list
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

class SalesViewSets(viewsets.GenericViewSet):
    queryset = Sales.objects.all()
    serializer_class = SalesSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Ventas'
    search_fields = ['id_sale','number_sale','client','date_sale','state','payment_method','subtotal','iva',
    'total','output_executing','return_executing','void','void_reason']

    @action(methods=['GET'],detail=False)
    def get_sales(self, request):
        try:    
            sales = self.get_queryset()
            if not sales:
                logger.warning(f'no se encontraron ventas')
                return Response({'message':'no existen ventas','success':False}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(sales,many=True)
            return Response({'message':'ventas obtenidas','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'ocurrio un error de servidor: {ex}')
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(methods=['GET'],detail=True)
    def get_sales_by_id(self, request, pk=None):
        try:
            sale = self.get_object()
            serializer = self.get_serializer(sale,many=False)
            logger.info(f'venta obtenida: {serializer.data}')
            return Response({'message':'venta obtenida','results':serializer.data,'success':True},status=status.HTTP_200_OK)
        except Sales.DoesNotExist as ne:
            logger.warning(f'la venta no existe: {ne}')
            return Response({'message':'Esta venta no existe', 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiple objetos retornados:{mo}')
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno de servidor: {ex}')
            return Response({'message':str(ex), 'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_sale(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            print(f'data: {request.data}')
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'venta creada exitosamente', 'success':True}, status=status.HTTP_201_CREATED)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}')
            return Response({'message':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,methods=['DELETE'])
    @transaction.atomic  
    def delete_sale(self, request, pk=None):
        try:
            sale = self.get_object()

            if not sale.state:
                return Response({'message': 'Solo se pueden eliminar ventas anuladas', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

            sale.delete()
            return Response({'message':'venta eliminada exitosamente','success':True}, status=status.HTTP_200_OK)
        except Sales.DoesNotExist as de:
            logger.warning(f'esta venta no esta disponible: {de}')
            return Response({'message':'esta venta no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos devueltos por el servidor: {mo}')
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_sales(self, request, pk=None):
        try:
            sale = self.get_object()
            serializer = self.get_serializer(sale, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'venta actualizada exitosamente','object':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Sales.DoesNotExist as de:
            logger.warning(f'esta venta no existe: {de}')
            return Response({'message':'esta venta no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos retornados por el servidor: {mo}')
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'ocurrio un error interno de servidor: {ex}')
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_sales(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response({'message':'ventas obtenidas','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['PATCH', 'POST'], url_path='patch_state')
    @transaction.atomic
    def annul_sale(self, request, pk=None):
        try:
            sale = self.get_object()
            if sale.state:
                return Response({'message': 'La venta ya está anulada', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

            sale.state = True
            void_reason = request.data.get('void_reason') or request.data.get('reason')
            if void_reason:
                sale.void_reason = void_reason
            sale.save()

            # Revertir stock para todos los detalles de la venta
            for detail in sale.sale_detail.all():
                add_stock(detail.variant, detail.quantity)
                logger.info(f'stock revertido para variante: {detail.variant.id_variant}, cantidad: {detail.quantity}')

            logger.info(f'venta anulada exitosamente')
            return Response({'message': 'venta anulada exitosamente', 'success': True}, status=status.HTTP_200_OK)
        except Sales.DoesNotExist as de:
            logger.warning(f'esta venta no esta disponible: {de}')
            return Response({'message': 'esta venta no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos devueltos por el servidor: {mo}')
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def export_sales(self, request):
        try:
            queryset = Sales.objects.select_related('client').prefetch_related('sale_detail__variant__product')
            list = Export_sales_list(queryset)

            return list
        except Exception as ex:
            return Response({'message':str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class SalesDetailViewsets(viewsets.ModelViewSet):
    queryset = SalesDetail.objects.all()
    serializer_class = SalesDetailsSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Ventas'
    search_fields = ['sale' , 'variant' ,'quantity' ,'unit_price' ,'subtotal' ,'creation_date',]

    @action(detail=True,methods=['GET'])
    def get_sales_by_id(self, request, pk=None):
        try:
            details = SalesDetail.objects.filter(sale=pk)
            if not details.exists():
                logger.warning(f'no se encontraron detaller en la compra')
                return Response({'message':'no hay detalles en esta venta','success':False},status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(details,many=True)
            return Response({'message':'detalle de la venta','results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message':str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_details(self, request):
        try:
            instances = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(instances, many=True)
            return Response({'message':'detalles encontrados','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor:{ex}')
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        

    

            


        

    
# Create your views here.
