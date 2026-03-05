from django.shortcuts import render
from rest_framework import filters,status,viewsets, views, permissions
from rest_framework.response import Response
from .models import Users, Typesdoc
from .serializers import UsersSerializer, UsersPatchActiveSerializer, TypesDocsSerializers,LoginSerializer, ChangePasswordSerializer, RequestOTPSerializer,ValidateOTPSerializer, ResetPasswordSerializer
from rest_framework.decorators import action
from django.core.exceptions import MultipleObjectsReturned
from django.db.utils import IntegrityError
from rest_framework.exceptions import ValidationError, APIException
from api.Exceptions.exceptions import ObjectNotExists,MultiResults, IntegrityException, InvalidData
from .Services.ExportUsers import Export_users_list
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi


class ChangePasswordView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        serializer = ChangePasswordSerializer(
            data=request.data,
            context={'request': request}
        )
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Contraseña cambiada exitosamente', 'success': True},
                status=status.HTTP_200_OK
            )
        return Response(
            {'errors': serializer.errors, 'success': False},
            status=status.HTTP_400_BAD_REQUEST
        )


class RequestOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = RequestOTPSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Código enviado al correo exitosamente', 'success': True},
                status=status.HTTP_200_OK
            )
        return Response(
            {'errors': serializer.errors, 'success': False},
            status=status.HTTP_400_BAD_REQUEST
        )


class ValidateOTPView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ValidateOTPSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Código validado correctamente', 'success': True},
                status=status.HTTP_200_OK
            )
        return Response(
            {'errors': serializer.errors, 'success': False},
            status=status.HTTP_400_BAD_REQUEST
        )


class ResetPasswordView(views.APIView):
    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response(
                {'message': 'Contraseña actualizada exitosamente', 'success': True},
                status=status.HTTP_200_OK
            )
        return Response(
            {'errors': serializer.errors, 'success': False},
            status=status.HTTP_400_BAD_REQUEST
        )
    
class LoginView(views.APIView):
    permission_classes = [permissions.AllowAny]

    @swagger_auto_schema(
        request_body=openapi.Schema(
            type=openapi.TYPE_OBJECT,
            required=['email', 'password'],
            properties={
                'email':    openapi.Schema(type=openapi.TYPE_STRING, example='admin@damabella.com'),
                'password': openapi.Schema(type=openapi.TYPE_STRING, example='Admin1234'),
            }
        )
    )
    def post(self, request):
        print('AUTH HEADER:', request.headers.get('Authorization'))
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            return Response(serializer.validated_data, status=status.HTTP_200_OK)
        return Response(
            {'success': False, 'errors': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST
        )

class UsersViewSets(viewsets.GenericViewSet):
    queryset = Users.objects.all()
    serializer_class = UsersSerializer
    # permission_classes = []
    # authentication_classes = []
    required_module = 'Users'
    filter_backends = [filters.SearchFilter]
    search_fields = ['doc_identity','name','email','phone','address','id_rol__name']

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return UsersPatchActiveSerializer
        return UsersSerializer

    @action(detail=False, methods=['GET'])
    def get_users(self, request):
        try:
            users = self.get_queryset()          
            serializer = self.get_serializer(users, many=True)
            return Response({'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Users.DoesNotExist:
            raise ObjectNotExists()
        except Exception as ex:
            raise APIException(detail=str(ex),code="error de servidor")
        
    @action(detail=True, methods=['GET'])
    def get_users_by_id(self, request, pk=None):
        try:
            user = self.get_object()
            serializer = self.get_serializer(user, many=False)
            return Response({'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Users.DoesNotExist:
            raise ObjectNotExists()
        except Exception as ex:
            raise APIException(detail=str(ex),code="error de servidor")
        
    @action(detail=False, methods=['POST'], permission_classes=[permissions.AllowAny])
    def create_users(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'creado exitosamente','object':serializer.data, 'success':True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            raise IntegrityException()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=True, methods=['DELETE'])
    def delete_users(self, request, pk=None):
        try:
            user = self.get_object()        
            user.delete()
            return Response({'results':'eliminado exitosamente', 'success':True}, status=status.HTTP_204_NO_CONTENT)
        except Users.DoesNotExist:
            raise ObjectNotExists()
        except IntegrityError:
            raise IntegrityException()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=True, methods=['PUT'])
    def update_users(self, request, pk=None):
        try:
            user = self.get_object()    
            data = request.data
            serializer = self.get_serializer(user, data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'actualizado exitosamente', 'User':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Users.DoesNotExist:
            raise ObjectNotExists()
        except ValidationError:
            raise InvalidData()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception:
            raise APIException(detail="Error interno del servidor",code="error de servidor")
        
        
    @action(detail=False, methods=['GET'], permission_classes = [permissions.AllowAny])
    def search_users(self, request):
        try:
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset=queryset)
            if not instance.exists():
                return Response({'message':'sin resultados', 'results':[], 'success':False}, status=status.HTTP_200_OK)
            
            serializer = self.get_serializer(instance, many=True)
            return Response({'message':'resultados obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=True, methods=['PATCH'])
    def change_state(self, request, pk=None):
        try:
            user = self.get_object()
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'results':'estado cambiado exitosamente','User':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except IntegrityError:
            raise IntegrityException()
        except ValidationError:
            raise InvalidData()
        except Users.DoesNotExist:
            raise ObjectNotExists()
        except Exception as ex:
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=False, methods=['GET'])   
    def export_users(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        return Export_users_list(queryset=queryset)
    
    
class TypesDocsViewSets(viewsets.GenericViewSet):
    queryset = Typesdoc.objects.all()
    serializer_class = TypesDocsSerializers
    permission_classes = [permissions.AllowAny]
    # authentication_classes = []

    @action(detail=False,methods=['GET'])
    def get_types_docs(self, request):
        try:
            types = self.get_queryset()
            serializer = self.get_serializer(types,many=True)
            return Response({'message':'tipos de documentos obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_types_docs_by_id(self, request, pk=None):
        try:
            type = self.get_object()
            serializer = self.get_serializer(type, many=False)
            return Response({'message':'tipo de documento obtenido', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Typesdoc.DoesNotExist:
            return Response({'message':'tipo de documento no encontrado', 'results':[], 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False,methods=['POST'])
    def create_types_docs(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'creado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message':'error de llaves','success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,methods=['DELETE'])
    def delete_types_docs(self, request, pk=None):
        try:
            type = self.get_object()
            type.delete()
            return Response({'message':'eliminado exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except Typesdoc.DoesNotExist:
            return Response({'message':'tipo no encontrado', 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos devueltos', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,methods=['PUT'])
    def update_types_docs(self, request, pk=None):
        try:
            type = self.get_object()
            serializer = self.get_serializer(type, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'actualizado exitosamente','type':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Typesdoc.DoesNotExist:
            return Response({'message':'este tipo no fue encontrado','success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
         


# Create your views here.
