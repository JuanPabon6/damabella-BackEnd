from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Returns, ReturnDetail, Changes, ChangesDetails
from .serializers import ReturnsSerializer, ReturnDetailSerializer, ChangesSerializer, ChangesDetailsSerializer
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from api.Inventory.services import add_stock
from .services import Export_returns_list
from django.http import HttpResponse
import logging
from django.db import transaction

logger = logging.getLogger(__name__)


# ==================== VIEWSETS PARA DEVOLUCIONES ====================

class ReturnsViewSets(viewsets.GenericViewSet):
    queryset = Returns.objects.all()
    serializer_class = ReturnsSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Devoluciones'
    search_fields = ['id_return', 'return_number', 'sale', 'return_date', 'reason', 'state', 'total', 'balance_in_favor', 'difference_to_pay']

    @action(methods=['GET'], detail=False)
    def get_returns(self, request):
        try:
            returns = self.get_queryset()
            if not returns.exists():
                logger.warning(f'no se encontraron devoluciones')
                return Response({'message': 'no existen devoluciones', 'success': False}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(returns, many=True)
            return Response({'message': 'devoluciones obtenidas', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'ocurrio un error de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['GET'], detail=True)
    def get_return_by_id(self, request, pk=None):
        try:
            return_obj = self.get_object()
            serializer = self.get_serializer(return_obj, many=False)
            logger.info(f'devolución obtenida: {serializer.data}')
            return Response({'message': 'devolución obtenida', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Returns.DoesNotExist as ne:
            logger.warning(f'la devolución no existe: {ne}')
            return Response({'message': 'Esta devolución no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiple objetos retornados: {mo}')
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    @transaction.atomic
    def create_return(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f'devolución creada exitosamente')
            return Response({'message': 'devolución creada exitosamente', 'success': True}, status=status.HTTP_201_CREATED)
        except IntegrityError as ie:
            logger.critical(f'error de integridad en base de datos: {ie}')
            return Response({'message': 'Error de integridad en los datos', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['DELETE'])
    @transaction.atomic
    def delete_return(self, request, pk=None):
        try:
            return_obj = self.get_object()

            if not return_obj.state:
                return Response({'message': 'Solo se pueden eliminar devoluciones anuladas', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

            return_obj.delete()
            logger.info(f'devolución eliminada exitosamente')
            return Response({'message': 'devolución eliminada exitosamente', 'success': True}, status=status.HTTP_200_OK)
        except Returns.DoesNotExist as de:
            logger.warning(f'esta devolución no esta disponible: {de}')
            return Response({'message': 'esta devolución no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos devueltos por el servidor: {mo}')
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['PATCH', 'POST'])
    @transaction.atomic
    def annul_return(self, request, pk=None):
        try:
            return_obj = self.get_object()
            if return_obj.state:
                return Response({'message': 'La devolución ya está anulada', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

            return_obj.state = True
            return_obj.save()

            # Revertir stock para todos los detalles de la devolución
            for detail in return_obj.return_detail.all():
                add_stock(detail.variant, detail.quantity)
                logger.info(f'stock revertido para variante: {detail.variant.id}, cantidad: {detail.quantity}')

            logger.info(f'devolución anulada exitosamente')
            return Response({'message': 'devolución anulada exitosamente', 'success': True}, status=status.HTTP_200_OK)
        except Returns.DoesNotExist as de:
            logger.warning(f'esta devolución no esta disponible: {de}')
            return Response({'message': 'esta devolución no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos devueltos por el servidor: {mo}')
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_returns(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response({'message': 'devoluciones obtenidas', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

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

    @action(detail=False, methods=['GET'])
    def export_all_returns(self, request):
        try:
            queryset = Returns.objects.select_related('sale').prefetch_related('return_detail__variant__product')
            file = Export_returns_list(queryset)
            return file
        except Exception as ex:
            logger.critical(f'error al exportar devoluciones: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['GET'])
    def export_return_by_id(self, request, pk=None):
        try:
            return_obj = self.get_object()
            queryset = Returns.objects.filter(id_return=pk).select_related('sale').prefetch_related('return_detail__variant__product')
            file = Export_returns_list(queryset)
            return file
        except Returns.DoesNotExist as de:
            logger.warning(f'devolución no encontrada para exportar: {de}')
            return Response({'message': 'esta devolución no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            logger.critical(f'error al exportar devolución: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReturnDetailViewsets(viewsets.ModelViewSet):
    queryset = ReturnDetail.objects.all()
    serializer_class = ReturnDetailSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Devoluciones'
    search_fields = ['return_id', 'variant', 'quantity', 'subtotal']

    @action(detail=True, methods=['GET'])
    def get_returns_by_id(self, request, pk=None):
        try:
            details = ReturnDetail.objects.filter(return_id=pk)
            if not details.exists():
                logger.warning(f'no se encontraron detalles en la devolución')
                return Response({'message': 'no hay detalles en esta devolución', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(details, many=True)
            return Response({'message': 'detalle de la devolución', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_details(self, request):
        try:
            instances = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(instances, many=True)
            return Response({'message': 'detalles encontrados', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== VIEWSETS PARA CAMBIOS ====================

class ChangesViewSets(viewsets.GenericViewSet):
    queryset = Changes.objects.all()
    serializer_class = ChangesSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Devoluciones'
    search_fields = ['id_change', 'change_number', 'sale', 'reason_of_change', 'state', 'stock_applied', 'return_applied']

    @action(methods=['GET'], detail=False)
    def get_changes(self, request):
        try:
            changes = self.get_queryset()
            if not changes.exists():
                logger.warning(f'no se encontraron cambios')
                return Response({'message': 'no existen cambios', 'success': False}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(changes, many=True)
            return Response({'message': 'cambios obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'ocurrio un error de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['GET'], detail=True)
    def get_change_by_id(self, request, pk=None):
        try:
            change_obj = self.get_object()
            serializer = self.get_serializer(change_obj, many=False)
            logger.info(f'cambio obtenido: {serializer.data}')
            return Response({'message': 'cambio obtenido', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Changes.DoesNotExist as ne:
            logger.warning(f'el cambio no existe: {ne}')
            return Response({'message': 'Este cambio no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiple objetos retornados: {mo}')
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    @transaction.atomic
    def create_change(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f'cambio creado exitosamente')
            return Response({'message': 'cambio creado exitosamente', 'success': True}, status=status.HTTP_201_CREATED)
        except IntegrityError as ie:
            logger.critical(f'error de integridad en base de datos: {ie}')
            return Response({'message': 'Error de integridad en los datos', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['DELETE'])
    @transaction.atomic
    def delete_change(self, request, pk=None):
        try:
            change_obj = self.get_object()
            current_state = change_obj.state.name_state

            if current_state != 'Anulado':
                return Response({'message': f'Solo se pueden eliminar cambios anulados', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

            # Revertir stock para todos los detalles del cambio si aplica
            if change_obj.stock_applied:
                for detail in change_obj.change_detail.all():
                    # Devolver el stock de la variante entregada
                    add_stock(detail.variant_delivered, 1)
                    logger.info(f'stock revertido para variante entregada: {detail.variant_delivered.id}')

            change_obj.delete()
            logger.info(f'cambio eliminado exitosamente')
            return Response({'message': 'cambio eliminado exitosamente', 'success': True}, status=status.HTTP_200_OK)
        except Changes.DoesNotExist as de:
            logger.warning(f'este cambio no esta disponible: {de}')
            return Response({'message': 'este cambio no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos devueltos por el servidor: {mo}')
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_changes(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response({'message': 'cambios obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_metrics(self, request):
        try:
            cantidad_cambios = Changes.objects.count()
            logger.info(f'métricas de cambios obtenidas')
            return Response({
                'message': 'métricas de cambios',
                'metrics': {
                    'cantidad_cambios': cantidad_cambios
                },
                'success': True
            }, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error al obtener métricas: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangesDetailViewsets(viewsets.ModelViewSet):
    queryset = ChangesDetails.objects.all()
    serializer_class = ChangesDetailsSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Devoluciones'
    search_fields = ['change', 'variant_returned', 'variant_delivered']

    @action(detail=True, methods=['GET'])
    def get_changes_by_id(self, request, pk=None):
        try:
            details = ChangesDetails.objects.filter(change=pk)
            if not details.exists():
                logger.warning(f'no se encontraron detalles en el cambio')
                return Response({'message': 'no hay detalles en este cambio', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(details, many=True)
            return Response({'message': 'detalle del cambio', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_details(self, request):
        try:
            instances = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(instances, many=True)
            return Response({'message': 'detalles encontrados', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Create your views here.
