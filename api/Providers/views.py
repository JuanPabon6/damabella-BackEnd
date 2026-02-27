from django.shortcuts import render
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from rest_framework.exceptions import APIException, ValidationError
from rest_framework.response import Response
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from api.Exceptions.exceptions import ObjectNotExists,MultiResults, IntegrityException, InvalidData
from .models import Providers
from .serializers import ProvidersSerializers

class ProvidersViewSets(viewsets.GenericViewSet):
    queryset = Providers.objects.all()
    serializer_class = ProvidersSerializers
    # authentication_classes = []
    # permission_classes = []
    filter_backends = [filters.SearchFilter]
    fields_search = ['nit_document','kompany_name','contact_name','phone','address']

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
    def get_providers_by_nit(self, request, pk=None):
        try:
            provider = self.get_object()
            serializer = self.get_serializer(provider,many=False)
            return Response({'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Providers.DoesNotExist:
            raise ObjectNotExists()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception as ex:
            raise APIException(detail=str(ex),code="error de servidor")
        
    @action(detail=False,methods=['POST'])
    def create_providers(self, request):
        try:
            data= request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'creado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except IntegrityError:
            raise IntegrityException()
        except ValidationError:
            raise InvalidData()
        except Exception as ex:
            raise APIException(detail=str(ex),code='error de servidor')
        
    @action(detail=True,methods=['DELETE'])
    def delete_providers(self, request, pk=None):
        try:
            provider = self.get_object()
            provider.delete()
            return Response({'results':'eliminado exitosamente','succes':True}, status=status.HTTP_200_OK)
        except Providers.DoesNotExist:
            raise ObjectNotExists()
        except IntegrityError:
            raise IntegrityException()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception as ex:
            raise APIException(detail=str(ex),code='error de servidor')
        
    @action(detail=True,methods=['PUT'])
    def update_providers(self, request, pk=None):
        try:
            provider = self.get_object()
            serializer = self.get_serializer(provider, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'actualizado exitosamente', 'provider':serializer.data, 'success':True})
        except MultipleObjectsReturned:
            raise MultiResults()
        except Providers.DoesNotExist:
            raise ObjectNotExists()
        except ValidationError:
            raise InvalidData()
        except IntegrityError:
            raise IntegrityException()
        except Exception as ex:
            raise APIException(detail=str(ex),code='error de servidor')
        
    @action(detail=False,methods=['GET'])
    def search_providers(self, request):
        try:
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset=queryset)
            if not instance.exists():
                return Response({'message':'sin resultados', 'results':[], 'success':False}, status=status.HTTP_200_OK)
            
            serializer = self.get_serializer(instance, many=True)
            return Response({'messsage':'resultados obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Providers.DoesNotExist:
            raise ObjectNotExists()
        except Exception as ex:
            raise APIException(detail=str(ex),code='error de servidor')
        

        

        


# Create your views here.
