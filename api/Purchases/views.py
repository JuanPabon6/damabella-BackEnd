from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Purchases, PurchaseDetail
from .serializers import PurchasesSerializer, PurchaseDetailSerializer
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from api.Inventory.services import out_stock
from api.States.models import States
from .services import Export_purchases_list

class PurchasesViewSet(viewsets.GenericViewSet):
    queryset = Purchases.objects.all()
    serializer_class = PurchasesSerializer
    required_module = 'Purchases'
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'purchase_number',
        'provider__name',
        'state__name',
        'observations',
        'total',
        'subtotal',
        'iva',
    ]

    @action(detail=False, methods=['GET'])
    def get_purchases(self, request):
        try:
            purchases = self.get_queryset()
            if not purchases.exists():
                return Response({'results': [], 'success': True}, status=status.HTTP_200_OK)
            serializer = self.get_serializer(purchases, many=True)
            return Response({'message': 'compras obtenidas', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['GET'])
    def get_purchase_by_id(self, request, pk=None):
        try:
            purchase = self.get_object()
            serializer = self.get_serializer(purchase)
            return Response({'message': 'compra obtenida', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Purchases.DoesNotExist:
            return Response({'message': 'compra no encontrada', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def create_purchase(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message': 'compra creada exitosamente', 'object': serializer.data, 'success': True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message': 'error de integridad en los datos', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['PUT'])
    def update_purchase(self, request, pk=None):
        try:
            purchase = self.get_object()
            serializer = self.get_serializer(purchase, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message': 'compra actualizada exitosamente', 'object': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Purchases.DoesNotExist:
            return Response({'message': 'compra no encontrada', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['PATCH'])
    def patch_state(self, request, pk=None):
        try:
            purchase = self.get_object()

            current_state = purchase.state.name_state
            if current_state in ['Entregado', 'Cancelado']:
                return Response({'message': f'No se puede cambiar el estado de una compra {current_state}','success': False}, status=status.HTTP_400_BAD_REQUEST)
            state_id = request.data.get('state')
            if not state_id:
                return Response({'message': 'estado requerido', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

            purchase.state_id_state = state_id
            purchase.save()
            serializer = self.get_serializer(purchase)
            return Response({'message': 'estado actualizado', 'object': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Purchases.DoesNotExist:
            return Response({'message': 'compra no encontrada', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            print('error de servidor:',ex)
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def get_purchase_by_provider(self, request):
        try:
            provider = request.query_params['provider']
            purchases = Purchases.objects.filter(provider=provider)
            serializer = self.get_serializer(purchases, many=True)
            return Response({'message':'compras obtenidas','results':serializer.data,'success':False},status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error de servidor':str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
            

    @action(detail=True, methods=['DELETE'])
    def delete_purchase(self, request, pk=None):
        try:
            purchase = self.get_object()

            current_state = purchase.state.name_state
            if current_state != 'Anulado':
                return Response({'message': f'Solo se pueden eliminar compras anuladas, Estado:{purchase.state.name_state}', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

            for detail in purchase.detail_purchase.all():
                out_stock(detail.variant, detail.quantity)

            purchase.delete()
            return Response({'message': 'compra eliminada exitosamente', 'success': True}, status=status.HTTP_200_OK)
        except Purchases.DoesNotExist:
            return Response({'message': 'compra no encontrada', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'message': 'error de integridad', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            print('error de servidor:',ex)
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_purchases(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            if not queryset.exists():
                return Response({'message': 'sin resultados', 'results': [], 'success': False}, status=status.HTTP_200_OK)
            serializer = self.get_serializer(queryset, many=True)
            return Response({'message': 'resultados obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def export_purchases(self, request):
        try:
            queryset = self.get_queryset().select_related('provider','state').prefetch_related('detail_purchase__variant__product')

            list = Export_purchases_list(queryset)
            return list
        except Exception as ex:
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class PurchaseDetailViewSet(viewsets.GenericViewSet):
    queryset = PurchaseDetail.objects.all()
    serializer_class = PurchaseDetailSerializer
    required_module = 'Purchases'
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'purchase__purchase_number',
        'variant__sku',
        'variant__product__name',
        'quantity',
        'purchase_price',
        'sales_price',
        'subtotal',
    ]

    @action(detail=False, methods=['GET'])
    def get_details(self, request):
        try:
            details = self.get_queryset()
            if not details.exists():
                return Response({'results': [], 'success': True}, status=status.HTTP_200_OK)
            serializer = self.get_serializer(details, many=True)
            return Response({'message': 'detalles obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['GET'])
    def get_detail_by_id(self, request, pk=None):
        try:
            detail = self.get_object()
            serializer = self.get_serializer(detail)
            return Response({'message': 'detalle obtenido', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except PurchaseDetail.DoesNotExist:
            return Response({'message': 'detalle no encontrado', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ─── GET detalles por compra ──────────────────────────────────────────────
    @action(detail=True, methods=['GET'])
    def get_details_by_purchase(self, request, pk=None):
        try:
            details = PurchaseDetail.objects.filter(purchase=pk)
            if not details.exists():
                return Response({'message': 'esta compra no tiene detalles', 'results': [], 'success': True}, status=status.HTTP_200_OK)
            serializer = self.get_serializer(details, many=True)
            return Response({'message': 'detalles obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_details(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            if not queryset.exists():
                return Response({'message': 'sin resultados', 'results': [], 'success': False}, status=status.HTTP_200_OK)
            serializer = self.get_serializer(queryset, many=True)
            return Response({'message': 'resultados obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)