from django.shortcuts import render
from rest_framework import status, viewsets, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from django.core.exceptions import MultipleObjectsReturned
from .serializers import ClientsSerializers, StateSerializer
from .models import Clients

class ClientsViewSets(viewsets.GenericViewSet):
    queryset = Clients.objects.all()
    serializer_class = ClientsSerializers
    # permission_classes = []
    # authentication_classes = []
    required_module = 'Clients'
    filter_backends = [filters.SearchFilter]
    search_fields = ['id_client','name','type_doc','doc','phone','address','email','state','city']

    def get_serializer_class(self):
        if self.action == 'patch_state':
            return StateSerializer
        return ClientsSerializers
    
    @action(detail=False,methods=['GET'])
    def get_clients(self, request):
        print('AUTH HEADER:', request.headers.get('Authorization'))
        print('USER:', request.user)
        clients = self.get_queryset()
        serializer = self.get_serializer(clients,many=True)
        return Response({'message':'clientes obtenidos','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
    
    @action(detail=True,methods=['GET'])
    def get_clients_by_id(self,request, pk=None):
        try:
            client = self.get_object()
            serializer = self.get_serializer(client,many=False)
            return Response({'message':'cliente obtenido', 'results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_clients(self, request):
        data = request.data
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({'message':'creado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_201_CREATED)
    
    @action(detail=True,methods=['DELETE'])
    def delete_clients(self,request, pk=None):
        try:
            client = self.get_object()
            client.delete()
            return Response({'message':'eliminado exitosamente','success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,methods=['PUT'])
    def update_clients(self, request, pk=None):
        try:
            client = self.get_object()
            serializer = self.get_serializer(client, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'cliente actualizado exitosamente', 'client':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PATCH'])
    def patch_state(self, request, pk=None):
        try:
            client = self.get_object()
            serializer = self.get_serializer(client, data=request.data,partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'estado actualizado exitosamente','object':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_clients(self, request):
        queryset = self.get_queryset()
        instance = self.filter_queryset(queryset=queryset)
        serializer = self.get_serializer(instance,many=True)
        return Response({'message':'clientes encontrados', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        

# Create your views here.
