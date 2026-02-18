from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Roles
from .serializers import RolesSerializers
from rest_framework.exceptions import APIException, ValidationError
from api.Exceptions.exceptions import ObjectNotExists,MultiResults, IntegrityException, InvalidData
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned

class RolesViewSets(viewsets.ModelViewSet):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializers
    permission_classes = []
    authentication_classes = []
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    action(detail=False, methods=['GET'])
    def get_roles(self, request, pk=None):
        try:
            roles = self.get_queryset()
            if not roles.exists():
                return Response({'results':[]}, status=status.HTTP_204_NO_CONTENT)
            
            serializer = self.get_serializer(roles, many=True)
            return Response({'results' : serializer.data}, status=status.HTTP_200_OK)
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    action(detail=True, methods=['GET'])    
    def get_rol_by_id(self, request, pk=None):
        try:
            rol = Roles.objects.get(id=pk)
            serializer = self.get_serializer(rol, many=False)
            return Response({'results': serializer.data}, status=status.HTTP_200_OK)
        except Roles.DoesNotExist:
            raise ObjectNotExists()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    action(detail=False, methods=['POST'])
    def create_roles(self, request, pk=None):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'creado exitosamente'}, status=status.HTTP_201_CREATED)
        except ValidationError:
            raise InvalidData()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    action(detail=True, methods=['DELETE'])
    def delete_rol(self, request, pk=None):
        try:
            rol = Roles.objects.get(id=pk)
            rol.delete()
            return Response({'results':'eliminado exitosamente'}, status=status.HTTP_204_NO_CONTENT)
        except Roles.DoesNotExist:
            raise ObjectNotExists()
        except IntegrityError:
            raise IntegrityException()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    action(detail=True, methods=['PUT'])
    def update_roles(self, request, pk=None):
        try:
            rol = self.get_object()
            serializer = self.get_serializer(rol, data=request.data)
            serializer.is_valid()
            serializer.save()
            return Response({'results':'actualizado exitosamente'}, status=status.HTTP_200_OK)
        except Roles.DoesNotExist:
            raise ObjectNotExists()
        except ValidationError:
            raise InvalidData()
        except IndentationError:
            raise IntegrityException()
        except Exception as ex: 
            raise APIException(detail=str(ex), code="error de servidor")
        
    action(detail=False, methods=['GET'])
    def search_roles(self, request, pk=None):
        try:
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset=queryset)
            if not instance.exists():
                return Response({'results':'Sin coincidencias', 'success':False}, status=status.HTTP_200_OK)
            
            serializer = self.get_serializer(instance, many=True)
            return Response({'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")



# Create your views here.
