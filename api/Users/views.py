from django.shortcuts import render
from rest_framework import filters,status,viewsets
from rest_framework.response import Response
from .models import Users
from .serializers import UsersSerializer, UsersPatchActiveSerializer
from rest_framework.decorators import action
from django.core.exceptions import MultipleObjectsReturned
from django.db.utils import IntegrityError
from rest_framework.exceptions import ValidationError, APIException
from api.Exceptions.exceptions import ObjectNotExists,MultiResults, IntegrityException, InvalidData

class UsersViewSets(viewsets.ModelViewSet):
    queryset = Users.objects.all()
    serializer_class = UsersSerializer
    permission_classes = []
    authentication_classes = []
    filter_backends = [filters.SearchFilter]
    search_fields = ['doc_identity','name','email','phone','address','id_rol__Name']

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return UsersPatchActiveSerializer
        return UsersSerializer

    action(detail=False, methods=['GET'])
    def get_users(self, request, pk=None):
        try:
            users = self.get_queryset()          
            serializer = self.get_serializer(users, many=True)
            return Response({'results':serializer.data}, status=status.HTTP_200_OK)
        except Users.DoesNotExist:
            raise ObjectNotExists()
        except Exception as ex:
            raise APIException(detail=str(ex),code="error de servidor")
        
    action(detail=True, methods=['GET'])
    def get_users_by_id(self, request, pk=None):
        try:
            user = Users.objects.get(Doc_identity=pk)
            serializer = self.get_serializer(user, many=False)
            return Response({'results':serializer.data}, status=status.HTTP_200_OK)
        except Users.DoesNotExist:
            raise ObjectNotExists()
        except Exception as ex:
            raise APIException(detail=str(ex),code="error de servidor")
        
    action(detail=False, methods=['POST'])
    def create_users(self, request, pk=None):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'creado exitosamente'}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            raise IntegrityException()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    action(detail=True, methods=['DELETE'])
    def delete_users(self, request, pk=None):
        try:
            user = Users.objects.get(Doc_identity=pk)        
            user.delete()
            return Response({'results':'eliminado exitosamente'}, status=status.HTTP_204_NO_CONTENT)
        except Users.DoesNotExist:
            raise ObjectNotExists()
        except IntegrityError:
            raise IntegrityException()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    action(detail=True, methods=['PUT'])
    def update_users(self, request, pk=None):
        try:
            user = Users.objects.get(Doc_identity=pk)     
            data = request.data
            serializer = self.get_serializer(user, data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'actualizado exitosamente'}, status=status.HTTP_200_OK)
        except Users.DoesNotExist:
            raise ObjectNotExists()
        except ValidationError:
            raise InvalidData()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception:
            raise APIException(detail="Error interno del servidor",code=500)
        
        
    action(detail=False, methods=['GET'])
    def search_users(self, request, pk=None):
        try:
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset=queryset)
            if not instance.exists():
                return Response({'results':[], 'success':False}, status=status.HTTP_200_OK)
            
            serializer = self.get_serializer(instance, many=True)
            return Response({'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    action(detail=True, methods=['PATCH'])
    def change_state(self, request, pk=None):
        try:
            user = Users.objects.get(Doc_identity=pk)
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'estado cambiado exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except IntegrityError:
            raise IntegrityException()
        except ValidationError:
            raise InvalidData()
        except Users.DoesNotExist:
            raise ObjectNotExists()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        


# Create your views here.
