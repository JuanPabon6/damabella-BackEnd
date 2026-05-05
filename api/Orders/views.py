from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Orders, OrdersDetail
from .serializers import OrdersSerializers, OrderDetailSerializer
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from .services import Export_orders_list
import logging

logger = logging.getLogger(__name__)

class OrdersViewSet(viewsets.GenericViewSet):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializers
    filter_backends = [filters.SearchFilter]
    search_fields = ['id_order','number_order','client','order_date','payment_method','address_shipment','person_receives','subtotal','iva','total','observations','state',
    ]

    @action(detail=False,methods=['GET'])
    def get_orders(self, request):
        try:
            orders = self.get_queryset()
            if not orders.exists():
                return Response({'message':'no se encontraron ordenes','success':False},status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(orders, many=True)
            return Response({'message':'pedidos obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno de servidor:{ex}')
            return Response({'message':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_orders_by_id(self, request, pk=None):
        try:
            order = self.get_object()
            serializer = self.get_serializer(order, many=False)
            return Response({'message':'pedido obtenido','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Orders.DoesNotExist:
            return Response({'message':'el pedido no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error de servidor:{ex}')
            return Response({'message':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False,methods=['POST'])
    def create_orders(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'creado exitosamente', 'object':serializer.data,'success':True}, status=status.HTTP_201_CREATED)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetosretornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            print('error de servidor',ex)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,methods=['DELETE'])
    def delete_orders(self, request, pk=None):
        try:
            order = self.get_object()
            order.delete()
            return Response({'message':'pedido eliminado','success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Orders.DoesNotExist:
            return Response({'message':'este pedido no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            print('error de servidor',ex)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_orders(self, request, pk=None):
        try:
            order = self.get_object()
            serializer = self.get_serializer(order, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'pedido actualizado exitosamente','object':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'mutliples objetos retornados','success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Orders.DoesNotExist:
            return Response({'message':'este pedido no existe','success':False},status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            print('error de servidor',ex)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PATCH'])
    def patch_state(self, request, pk=None):
        try:
            order = self.get_object()
            state_id = request.data.get('state')
            if not state_id:
              return Response({'message':'no hay estado para asignar','success':False},status=status.HTTP_400_BAD_REQUEST)
            order.state_id_state = state_id
            order.save()
            serializer = self.get_serializer(order)
            return Response({'message':'estado actualizado', 'object':serializer.data, 'success':True},status=status.HTTP_200_OK)
        except Orders.DoesNotExist:
            return Response({'message':'este pedido no existe','success':False},status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            print('error de servidor:',ex)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_orders(self, request):
        try:
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset)
            serializer = self.get_serializer(instance,many=True)
            return Response({'message':'resultados obtenidos','results':serializer.data,'success':True},status=status.HTTP_200_OK)
        except Exception as ex:
            print('error de servidor:',ex)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def export_orders(self, request):
        try:
            queryset = Orders.objects.select_related('client','payment_method','state').prefetch_related('detail_order__variant__product')

            list = Export_orders_list(queryset) 
            return list
        except Exception as ex:
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class OrdersDetailsViewSet(viewsets.GenericViewSet):
    queryset = OrdersDetail.objects.all()
    serializer_class = OrderDetailSerializer
    filter_backends = [filters.SearchFilter]
    search_fields = ['id_detail','order','variant','quantity','sales_price','subtotal']

    @action(detail=False,methods=['GET'])
    def get_details(self, request):
        try:
            details = self.get_queryset()
            serializer = self.get_serializer(details,many=True)
            return Response({'message':'detalles obtenidos', 'results':serializer.data,'success':True},status=status.HTTP_200_OK)
        except ValueError as ve:
            logger.error(f'error de valores: {ve}', exc_info=True)
            return Response({'message':'error de valores','success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}', exc_info=True)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_details_by_id(self, request, pk=None):
        try:
            detail = self.get_object()
            serializer = self.get_serializer(detail,many=False)
            return Response({'message':'detalle obtenido','results':serializer.data,'success':True},status=status.HTTP_200_OK)
        except OrdersDetail.DoesNotExist as ne:
            logger.error(f'error de detalle: {ne}', exc_info=True)
            return Response({'message':'el detalle no existe','success':False},status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos devueltos: {mo}', exc_info=True)
            return Response({'message':'multiples objetos retornados','success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}', exc_info=True)
            return Response({'message':str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_details_by_order(self, request, pk=None):
        try:
            details = OrdersDetail.objects.filter(order=pk)
            if not details.exists():
                return Response({'message':'no se encontraron detalles','success':False},status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(details,many=True)
            return Response({'message':'detalles obtenidos','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except ValueError as ve:
            logger.error(f'erro de valor: {ve}', exc_info=True)
            return Response({'message':'error de valores','success':False},status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}', exc_info=True)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_details(self,request):
        try:
            queryset = self.get_queryset()
            if not queryset.exists():
                return Response({'message':'no hay detalles','success':False}, status=status.HTTP_400_BAD_REQUEST)
            instance = self.filter_queryset(queryset)
            serializer = self.get_serializer(instance,many=True)
            return Response({'message':'detalles encontrados','results':serializer.data,'success':True},status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}', exc_info=True)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

        

        
    

# Create your views here.
