from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Roles, Permissions
from .serializers import RolesSerializers, PermissionsSerializer, PatchStateRolesSerializer
from rest_framework.exceptions import APIException, ValidationError
from api.Exceptions.exceptions import ObjectNotExists,MultiResults, IntegrityException, InvalidData
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned

class RolesViewSets(viewsets.GenericViewSet):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializers
    # permission_classes = []
    # authentication_classes = []
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return PatchStateRolesSerializer
        return RolesSerializers


    @action(detail=False, methods=['GET'])
    def get_roles(self, request):
        try:
            roles = self.get_queryset()
            if not roles.exists():
                return Response({'results':[]}, status=status.HTTP_204_NO_CONTENT)
            
            serializer = self.get_serializer(roles, many=True)
            return Response({'results' : serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=True, methods=['GET'])    
    def get_rol_by_id(self, request, pk=None):
        try:
            rol = self.get_object()
            serializer = self.get_serializer(rol, many=False)
            return Response({'results': serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Roles.DoesNotExist:
            raise ObjectNotExists()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=False, methods=['POST'])
    def create_roles(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'creado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_201_CREATED)
        except ValidationError:
            raise InvalidData()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=True, methods=['DELETE'])
    def delete_rol(self, request, pk=None):
        try:
            rol = self.get_object()
            rol.delete()
            return Response({'results':'eliminado exitosamente', 'success':True}, status=status.HTTP_204_NO_CONTENT)
        except Roles.DoesNotExist:
            raise ObjectNotExists()
        except IntegrityError:
            raise IntegrityException()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=True, methods=['PUT'])
    def update_roles(self, request, pk=None):
        try:
            rol = self.get_object()
            serializer = self.get_serializer(rol, data=request.data)
            serializer.is_valid()
            serializer.save()
            return Response({'results':'actualizado exitosamente', 'rol':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Roles.DoesNotExist:
            raise ObjectNotExists()
        except ValidationError:
            raise InvalidData()
        except IndentationError:
            raise IntegrityException()
        except Exception as ex: 
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=False, methods=['GET'])
    def search_roles(self, request):
        try:
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset=queryset)
            if not instance.exists():
                return Response({'message':'sin resultados', 'results':[], 'success':False}, status=status.HTTP_200_OK)
            
            serializer = self.get_serializer(instance, many=True)
            return Response({'message':'resultados obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=True,methods=['PATCH'])
    def change_state(self, request, pk=None):
        try:
            permission = self.get_object()
            if not permission.exists():
                return Response({'message':'permiso no encontrado', 'results':[], 'success':False}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer_class(permission, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'estado cambiado exitosamente','permission':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos devueltos', 'results':[], 'success':False})
        except Exception as ex:
            return Response({'error':str(ex), 'success':False})


class PermissionsViewSets(viewsets.GenericViewSet):
    queryset = Permissions.objects.all()
    serializer_class = PermissionsSerializer
    # authentication_classes = []
    # permission_classes = []

    @action(detail=True,methods=['GET'])
    def get_permissions(self, request):
        try:
            permissions = self.get_queryset()
            serializer = self.get_serializer(permissions,many=True)
            return Response({'message':'permisos obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,methods=['GET'])
    def get_permissions_by_id(self, request, pk=None):
        try:
            permission = self.get_object()
            serializer = self.get_serializer(permission,many=False)
            return Response({'message':'permiso obtenido', 'results':serializer.data, 'success':True}) 
        except Permissions.DoesNotExist:
            return Response({'message':'no se encontraron permisos', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False,methods=['POST'])
    def create_permissions(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'creado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message':'error de llaves', 'results':[], 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_permissions(self, request, pk=None):
        try:
            permission = self.get_object()
            permission.delete()
            return Response({'message':'eliminado exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except IntegrityError:
            return Response({'message':'error de llaves', 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'errors':str(ex), 'success':False})
        
    @action(detail=True,methods=['PUT'])
    def update_permissions(self, request, pk=None):
        try:
            permission = self.get_object()
            serializer = self.get_serializer(permission, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'actualizado exitosamente', 'permission':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Permissions.DoesNotExist:
            return Response({'message':'este permiso no existe', 'results':[], 'success':False})
        except MultipleObjectsReturned:
            return Response({'message':'multiples resultados devueltos', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

# Create your views here.
