from django.shortcuts import render
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from api.Exceptions.exceptions import ObjectNotExists,MultiResults, IntegrityException, InvalidData
from .models import Providers
from .serializers import ProvidersSerializers, PatchStateSerializer

class ProvidersViewSets(viewsets.GenericViewSet):
    queryset = Providers.objects.all()
    serializer_class = ProvidersSerializers
    # authentication_classes = []
    # permission_classes = []
    required_module = 'Proveedores'
    filter_backends = [filters.SearchFilter]
    fields_search = ['nit_document','kompany_name','contact_name','phone','address']

    def get_serializer_class(self):
        if self.action == 'patch_state':
            return PatchStateSerializer
        return ProvidersSerializers

    @action(detail=False, methods=['GET'])
    def get_providers(self, request):
        try:
            providers = self.get_queryset()
            serializer = self.get_serializer(providers,many=True)
            return Response({'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Providers.DoesNotExist:
            raise ObjectNotExists()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=True, methods=['GET'])    
    def get_providers_by_id(self, request, pk=None):
            try:
                provider = self.get_object()
                serializer = self.get_serializer(provider,many=False)
                return Response({'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
            except MultipleObjectsReturned:
                return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_providers(self, request):
        try:
            data= request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'creado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_providers(self, request, pk=None):
        try:
            provider = self.get_object()
            provider.delete()
            return Response({'results':'eliminado exitosamente','succes':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except IntegrityError:
            return Response({'message':'No se puede eliminar el proveedor porque tiene compras asociadas.', 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'message':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_providers(self, request, pk=None):
        try:
            provider = self.get_object()
            serializer = self.get_serializer(provider, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'actualizado exitosamente', 'provider':serializer.data, 'success':True})
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_providers(self, request):
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset=queryset)
            if not instance.exists():
                return Response({'message':'sin resultados', 'results':[], 'success':False}, status=status.HTTP_200_OK)
            
            serializer = self.get_serializer(instance, many=True)
            return Response({'message':'resultados obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)

    @action(detail=True,methods=['PATCH'])
    def patch_state(self, request, pk=None):
        try:
            provider = self.get_object()
            serializer = self.get_serializer(provider, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'estado cambiado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['GET'])
    def purchase_history(self, request, pk=None):
        try:
            from api.Purchases.models import Purchases, PurchaseDetail
            from api.Purchases.serializers import PurchasesSerializer
            from django.db.models import Sum

            provider = self.get_object()
            purchases = Purchases.objects.filter(provider=provider, canceled=False)

            total_purchases = purchases.count()

            total_qty_agg = PurchaseDetail.objects.filter(
                purchase__provider=provider,
                purchase__canceled=False
            ).aggregate(total_qty=Sum('quantity'))
            total_products_received = total_qty_agg['total_qty'] or 0

            total_amount_agg = purchases.aggregate(total_sum=Sum('total'))
            total_amount_accumulated = total_amount_agg['total_sum'] or 0.0

            serializer = PurchasesSerializer(purchases, many=True)

            return Response({
                'success': True,
                'stats': {
                    'total_purchases': total_purchases,
                    'total_products_received': total_products_received,
                    'total_amount_accumulated': float(total_amount_accumulated)
                },
                'results': serializer.data
            }, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

        


# Create your views here.
