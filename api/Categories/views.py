from django.shortcuts import render
from rest_framework import viewsets,status,filters
from rest_framework.response import Response
from rest_framework.exceptions import APIException,ValidationError
from rest_framework.decorators import action
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from .models import Categories
from .serializers import CategoriesSerializers, PatchStateCategoriesSerializers
from api.Exceptions.exceptions import ObjectNotExists,MultiResults, IntegrityException, InvalidData

class CategoriesViewSets(viewsets.GenericViewSet):
    queryset = Categories.objects.all()
    serializer_class = CategoriesSerializers
    permission_classes = []
    authentication_classes = []
    filter_backends = [filters.SearchFilter]
    fields_search = ['id_category','name','description','is_active']

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return PatchStateCategoriesSerializers
        return CategoriesSerializers

    @action(detail=False, methods=['GET'])
    def get_categories(self, request):
        try:
            categories = self.get_queryset()
            if not categories.exists:
                return Response({'message':'no se encontraron resultados','results':[], 'success':True}, status=status.HTTP_404_NOT_FOUND)
            serialzier = self.get_serializer(categories,many=True)
            return Response({'results':serialzier.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['GET'])
    def get_categories_by_id(self, request, pk=None):
        try:
            category = self.get_object()
            serializer = self.get_serializer(category,many=False)
            return Response({'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Categories.DoesNotExist:
            return Response({'message': 'No se encontraron resultados','results': [],'success': True}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos devueltos','results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_categories(self, request):
        try:
            data  = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'creado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_201_CREATED)
        # except ValidationError:
        #     return Response({'message':'datos incorrectos enviados', 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except IntegrityError:
            return Response({'message':'error de llaves e integridad de datos enviados', 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_categories(self, request, pk=None):
        try:
            category = self.get_object()
            category.delete()
            return Response({'results':'eliminado exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except Categories.DoesNotExist:
            return Response({'message': 'No se encontraron resultados','results': [],'success': True}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos devueltos','results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_categories(self, request, pk=None):
        try:
            category = self.get_object()
            serializer = self.get_serializer(category, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'actualizado exitosamente','category':serializer.data, 'success':True})
        except Categories.DoesNotExist:
            return Response({'message':'categoria no encontrada', 'results':[], 'success':False})
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos devueltos','results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
             return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_categories(self, request):
        try:
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset=queryset)
            serializer = self.get_serializer(instance,many=True)
            return Response({'message':'categorias obtenidas', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    @action(detail=True,methods=['PATCH'])
    def change_state(self, request, pk=None):
        try:
            category = self.get_object()
            serializer = self.get_serializer_class(category, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'estado actualizado exitosamente', 'categoria':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos devueltos', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except IntegrityError:
            return Response({'message':'error de llaves', 'results':[], 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   
        
        # Create your views here.
