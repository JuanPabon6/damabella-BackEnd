from django.shortcuts import render
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.core.exceptions import MultipleObjectsReturned
from .models import States
from .serializers import StatesSerializers

class StatesViewSets(viewsets.GenericViewSet):
    queryset = States.objects.all()
    required_module = 'Estados'
    serializer_class = StatesSerializers
    permission_classes = [permissions.AllowAny]

    @action(detail=False,methods=['GET'])
    def get_states(self, request):
        states = self.get_queryset()
        serializer = self.get_serializer(states, many=True)
        return Response({'message':'estados obtenidos','results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
    
    @action(detail=True,methods=['GET'])
    def get_states_by_id(self, request, pk=None):
        try:
            state = self.get_object()
            serializer = self.get_serializer(state,many=False)
            return Response({'message':'estado obtenido','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_states(self, request):
            try:
                data = request.data
                serializer = self.get_serializer(data=data)
                serializer.is_valid(raise_exception=True)
                serializer.save()
                return Response({'message':'estado creado exitosamente', 'object':serializer.data,'success':True}, status=status.HTTP_201_CREATED)
            except MultipleObjectsReturned:
                return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=True,methods=['DELETE'])
    def delete_states(self, request, pk=None):
        try:
              state = self.get_object()
              state.delete()
              return Response({'message':'estado eliminado exitosamente','success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
             return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_states(self, request, pk=None):
        try:
            state = self.get_object()
            serializer = self.get_serializer(state, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'actualizado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
             return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# Create your views here.
