from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import viewsets,status
from rest_framework.decorators import action
from .models import Inventory
from .serializers import InventorySerializers, AdjustStockSerializer
from .services import add_stock,out_stock
from django.core.exceptions import MultipleObjectsReturned
from django.shortcuts import get_object_or_404

class InventoryViewSets(viewsets.GenericViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializers
    # permission_classes = []
    # authentication_classes = []

    def get_serializer_class(self):
        if self.action in ['increment_stock','subtract_stock']:
            return AdjustStockSerializer
        return InventorySerializers

    @action(detail=False,methods=['GET'])
    def get_inventories(self, request):
        inventories = self.get_queryset()
        serializer = self.get_serializer(inventories,many=True)
        return Response({'message':'inventarios obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)

    @action(detail=True,methods=['GET'])
    def get_Inventory_by_id(self, request, pk=None):
        try:
            inventory = self.get_object()
            serializer = self.get_serializer(inventory,many=False)
            return Response({'message':'inventario obtenido', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos rotornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['POST'])
    def increment_stock(self, request, pk=None):
        inventory = get_object_or_404(Inventory, variant=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        add_stock(inventory.variant, serializer.validated_data['amount'])
        return Response({'message':'stock sumado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_200_OK)
    
    @action(detail=True,methods=['POST'])
    def subtract_stock(self, request, pk=None):
        inventory = get_object_or_404(Inventory, variant=pk)
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        out_stock(inventory.variant, serializer.validated_data['amount'])
        return Response({'message':'stock ajustado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_200_OK)
    
        
        # Create your views here.
