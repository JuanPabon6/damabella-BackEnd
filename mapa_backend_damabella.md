# MAPA DE ARQUITECTURA BACKEND - DAMABELLA

Este archivo contiene las rutas y vistas del backend para la integración móvil.

## ARCHIVO: .\api\urls.py
```python
from django.urls import path,include

urlpatterns = [
    path('', include('api.Roles.urls')),
    path('', include('api.Users.urls')),
    path('', include('api.Providers.urls')),
    path('', include('api.Categories.urls')),
    path('', include('api.Products.urls')),
    path('', include('api.Inventory.urls')),
    path('', include('api.Clients.urls')),
    path('', include('api.Purchases.urls')),
    path('', include('api.States.urls')),
    path('', include('api.Orders.urls')),
    path('', include('api.Sales.urls')),
    path('', include('api.Dashboard.urls')),
    path('', include('api.Returns.urls')),
]
```

## ARCHIVO: .\api\views.py
```python
from django.shortcuts import render

# Create your views here.

```

## ARCHIVO: .\api\Authentication\views.py
```python
from django.shortcuts import render

# Create your views here.

```

## ARCHIVO: .\api\Categories\urls.py
```python
from rest_framework import routers
from django.urls import path,include
from .views import CategoriesViewSets

router = routers.DefaultRouter()
router.register(r'categories', CategoriesViewSets, basename='categories')

urlpatterns = [
    path('', include(router.urls))
]
```

## ARCHIVO: .\api\Categories\views.py
```python
from django.shortcuts import render
from rest_framework import viewsets,status,filters, permissions
from rest_framework.response import Response
from rest_framework.exceptions import APIException,ValidationError
from rest_framework.decorators import action
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from .models import Categories
from .serializers import CategoriesSerializers, PatchStateCategoriesSerializers
from api.Exceptions.exceptions import ObjectNotExists,MultiResults, IntegrityException, InvalidData
from api.Products.models import Products

class CategoriesViewSets(viewsets.GenericViewSet):
    queryset = Categories.objects.all()
    serializer_class = CategoriesSerializers
    permission_classes = [permissions.AllowAny]
    # authentication_classes = []
    required_module = 'Categorias'
    filter_backends = [filters.SearchFilter]
    fields_search = ['id_category','name','description','is_active']

    def get_serializer_class(self):
        if self.action == 'change_state':
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
            serializer = self.get_serializer(category, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'estado actualizado exitosamente', 'categoria':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos devueltos', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except IntegrityError:
            return Response({'message':'error de llaves', 'results':[], 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)   

    @action(detail=True,methods=['GET'])
    def get_products_by_category(self, request, pk=None):
        try:
            products = Products.objects.filter(category=pk)
            serializer = self.get_serializer(products, many=True)
            return Response({'message':'productos obtenidos','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        # Create your views here.

```

## ARCHIVO: .\api\Clients\urls.py
```python
from rest_framework import routers
# from .views import ClientsViewSets
from django.urls import path, include

router = routers.DefaultRouter()


urlpatterns = [
    path('', include(router.urls))
]
```

## ARCHIVO: .\api\Clients\views.py
```python

```

## ARCHIVO: .\api\Dashboard\urls.py
```python
from rest_framework import routers
from django.urls import path,include
from .views import DashboardViewSets

router = routers.DefaultRouter()

router.register(r'dashboard',DashboardViewSets,basename='dashboard')

urlpatterns =[
    path('', include(router.urls))
]
```

## ARCHIVO: .\api\Dashboard\views.py
```python
from django.shortcuts import render
from rest_framework import viewsets, status, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
import logging
from api.Sales.models import Sales, SalesDetail
from api.Sales.serializers import SalesDetailsSerializer, SalesSerializer
from api.Orders.models import Orders, OrdersDetail
from api.Orders.serializers import OrderDetailSerializer, OrdersSerializers
from api.Users.models import Users
from api.Users.serializers import UsersSerializer
from api.Sales.models import Sales, SalesDetail
from api.Sales.serializers import SalesSerializer, SalesDetailsSerializer
from api.Returns.models import Returns
from django.utils import timezone
from django.db.models import Sum, Count
from datetime import datetime

logger = logging.getLogger(__name__)


class DashboardViewSets(viewsets.GenericViewSet):

    @action(detail=False,methods=['GET'])
    def get_users_active(self, request):
        try:
            active = True

            users_active = Users.objects.filter(is_active=active).count()
            # serializer = UsersSerializer(users_active, many=True)
            return Response({'results':users_active, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def get_pending_orders(self, request):
        try:
            orders = Orders.objects.filter(state__name_state="Pendiente").count()
            # serializer = OrdersSerializers(orders, many=True)
            return Response({'results':orders, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'])
    def cantidad_ventas_mes(self, request):
        try:
            # Obtener fecha actual
            now = timezone.now()
            mes_actual = now.month
            año_actual = now.year
            
            cantidad = Sales.objects.filter(date_sale__month=mes_actual,date_sale__year=año_actual).count()
            
            return Response({'success': True,'results': cantidad}, status=status.HTTP_200_OK)
            
        except Exception as ex:
            return Response({'success': False,'error': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(detail=False, methods=['get'])
    def dinero_ventas_mes(self, request):
        try:
            now = timezone.now()
            mes_actual = now.month
            año_actual = now.year
            
            resultado = Sales.objects.filter(date_sale__month=mes_actual,date_sale__year=año_actual).aggregate(total_dinero=Sum('total'))
            
            total = resultado['total_dinero'] or 0
            
            return Response({'success': True,'results': float(total)}, status=status.HTTP_200_OK)
            
        except Exception as e:
            return Response({'success': False,'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'])
    def productos_mas_vendidos(self, request):
        try:
            top_productos = SalesDetail.objects.values('variant__product__name')\
                .annotate(total_vendido=Sum('quantity'))\
                .order_by('-total_vendido')[:5]
            
            resultados = [
                {
                    'producto': item['variant__product__name'],
                    'cantidad': item['total_vendido']
                } for item in top_productos
            ]
            
            print(resultados)
            return Response({'success': True, 'results': resultados}, status=status.HTTP_200_OK)
            
        except Exception as ex:
            print(ex)
            return Response({'success': False, 'error': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False, methods=['get'])
    def distribucion_categorias(self, request):
        try:
            # Calcular total general desde SalesDetail
            total_general = SalesDetail.objects.aggregate(total_todo=Sum('subtotal'))['total_todo'] or 0
            
            if total_general == 0:
                return Response({'success': True, 'results': []}, status=status.HTTP_200_OK)

            categorias_data = SalesDetail.objects.values('variant__product__category__name')\
                .annotate(total_categoria=Sum('subtotal'))\
                .order_by('-total_categoria')

            resultados = []
            for item in categorias_data:
                total_cat = item['total_categoria'] or 0
                porcentaje = (total_cat * 100) / total_general
                
                resultados.append({
                    'categoria': item['variant__product__category__name'],
                    'total_vendido': float(total_cat),
                    'porcentaje': round(float(porcentaje), 2)
                })
            print(resultados)

            return Response({'success': True, 'results': resultados}, status=status.HTTP_200_OK)
            
        except Exception as ex:
            print(ex)
            return Response({'success': False, 'error': str(ex)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_metrics(self, request):
        try:
            cantidad_devoluciones = Returns.objects.count()
            logger.info(f'métricas de devoluciones obtenidas')
            return Response({
                'message': 'métricas de devoluciones',
                'metrics': {
                    'cantidad_devoluciones': cantidad_devoluciones
                },
                'success': True
            }, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error al obtener métricas: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)



# Create your views here.

```

## ARCHIVO: .\api\Inventory\urls.py
```python
from rest_framework import routers
from django.urls import path, include
from .views import InventoryViewSets

router = routers.DefaultRouter()
router.register(r'inventory', InventoryViewSets, basename='inventory')

urlpatterns = [
    path('', include(router.urls))
]
```

## ARCHIVO: .\api\Inventory\views.py
```python
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import viewsets,status, permissions
from rest_framework.decorators import action
from .models import Inventory
from .serializers import InventorySerializers, AdjustStockSerializer
from .services import add_stock,out_stock
from django.core.exceptions import MultipleObjectsReturned
from django.shortcuts import get_object_or_404

class InventoryViewSets(viewsets.GenericViewSet):
    queryset = Inventory.objects.all()
    serializer_class = InventorySerializers
    permission_classes = [permissions.AllowAny]
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
    def get_inventory_by_id(self, request, pk=None):
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

```

## ARCHIVO: .\api\Orders\urls.py
```python
from rest_framework import routers
from django.urls import include,path
from .views import OrdersDetailsViewSet, OrdersViewSet, PaymentMethodsViewSet

router = routers.DefaultRouter()

router.register(r'orders',OrdersViewSet,basename='orders')
router.register(r'ordersdetail',OrdersDetailsViewSet,basename='ordersdetail')
router.register(r'paymentmethods', PaymentMethodsViewSet, basename='paymentmethods')

urlpatterns= [
path('', include(router.urls))
]
```

## ARCHIVO: .\api\Orders\views.py
```python
from django.shortcuts import render
from rest_framework import viewsets, status, filters, permissions
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Orders, OrdersDetail, PaymentMethods
from .serializers import OrdersSerializers, OrderDetailSerializer, PaymentMethodsSerializer
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from api.States.models import States
from .services import Export_orders_list
import logging

logger = logging.getLogger(__name__)

class OrdersViewSet(viewsets.GenericViewSet):
    queryset = Orders.objects.all()
    serializer_class = OrdersSerializers
    filter_backends = [filters.SearchFilter]
    permission_classes = [permissions.AllowAny]
    required_module = 'Pedidos'
    search_fields = ['id_order','number_order','client','order_date','payment_method','address_shipment','person_receives','subtotal','iva','total','observations','state',
    ]

    @action(detail=False,methods=['GET'])
    def get_orders(self, request):
        try:
            orders = self.get_queryset()
            if not orders.exists():
                return Response({'message':'no se encontraron ordenes','success':False},status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(orders, many=True)
            return Response({'message':'pedidos obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno de servidor:{ex}')
            return Response({'message':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_orders_by_id(self, request, pk=None):
        try:
            order = self.get_object()
            serializer = self.get_serializer(order, many=False)
            return Response({'message':'pedido obtenido','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Orders.DoesNotExist:
            return Response({'message':'el pedido no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error de servidor:{ex}')
            return Response({'message':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False,methods=['POST'])
    def create_orders(self, request):
        try:
            print(f'data enviada: {request.data}')
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'creado exitosamente', 'object':serializer.data,'success':True}, status=status.HTTP_201_CREATED)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetosretornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            print('error de servidor',ex)
            print(f'campos de errores: {serializer.errors}')
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,methods=['DELETE'])
    def delete_orders(self, request, pk=None):
        try:
            order = self.get_object()
            order.delete()
            return Response({'message':'pedido eliminado','success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Orders.DoesNotExist:
            return Response({'message':'este pedido no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            print('error de servidor',ex)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_orders(self, request, pk=None):
        try:
            order = self.get_object()
            serializer = self.get_serializer(order, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'pedido actualizado exitosamente','object':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'mutliples objetos retornados','success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Orders.DoesNotExist:
            return Response({'message':'este pedido no existe','success':False},status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            print('error de servidor',ex)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True, methods=['PATCH'])
    def patch_state(self, request, pk=None):
        try:
            order = self.get_object()
            state_id = request.data.get('state')
            
            if not state_id:
                return Response({
                    'message': 'no hay estado para asignar', 
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)
                
            try:
                # 1. Buscamos el objeto de estado real usando su llave primaria id_state
                state_obj = States.objects.get(id_state=state_id)
                
                # 2. Asignamos el objeto directamente a la relación 'state' definida en tu modelo Orders
                order.state = state_obj
                order.save()
                
            except States.DoesNotExist:
                return Response({
                    'message': f'El estado con ID {state_id} no existe en la base de datos', 
                    'success': False
                }, status=status.HTTP_400_BAD_REQUEST)

            # 3. Serializamos el pedido actualizado para retornar los datos frescos al Front
            serializer = self.get_serializer(order)
            return Response({
                'message': 'estado actualizado', 
                'object': serializer.data, 
                'success': True
            }, status=status.HTTP_200_OK)
            
        except Orders.DoesNotExist:
            return Response({
                'message': 'este pedido no existe', 
                'success': False
            }, status=status.HTTP_404_NOT_FOUND)
            
        except MultipleObjectsReturned:
            return Response({
                'message': 'multiples objetos retornados', 
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
        except Exception as ex:
            print('error de servidor:', ex)
            return Response({
                'message': str(ex), 
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_orders(self, request):
        try:
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset)
            serializer = self.get_serializer(instance,many=True)
            return Response({'message':'resultados obtenidos','results':serializer.data,'success':True},status=status.HTTP_200_OK)
        except Exception as ex:
            print('error de servidor:',ex)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def export_orders(self, request):
        try:
            queryset = Orders.objects.select_related('client','payment_method','state').prefetch_related('detail_order__variant__product')

            list = Export_orders_list(queryset) 
            return list
        except Exception as ex:
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'], permission_classes=[permissions.IsAuthenticated])
    def get_my_orders(self, request):
        """
        Retorna las órdenes del usuario autenticado. 
        Si no tiene perfil de cliente, se le crea uno usando sus datos de usuario de forma segura.
        """
        try:
            # Importación segura de tu app de clientes
            from api.Users.models import Clients  
            
            # 1. Buscamos el cliente (insensible a mayúsculas/minúsculas)
            try:
                current_client = Clients.objects.get(email__iexact=request.user.email)
            except Clients.DoesNotExist:
                # 🛠️ Quitamos 'username' para evitar el AttributeError
                # Si request.user no tiene 'name', usará la primera parte del correo como nombre temporal
                default_name = getattr(request.user, 'name', request.user.email.split('@')[0])
                
                current_client = Clients.objects.create(
                    name=default_name,
                    email=request.user.email,
                    phone=getattr(request.user, 'phone', '0000000000'),
                    address=getattr(request.user, 'address', ''),
                    city='Medellín',
                    doc=getattr(request.user, 'doc_identity', '00000000'),
                    type_doc_id=1,
                    state=True
                )

            # 2. Filtramos los pedidos de este cliente
            orders = Orders.objects.filter(client=current_client).order_by('-order_date')
            
            if not orders.exists():
                return Response({
                    'message': 'No tienes pedidos registrados todavía',
                    'results': [],
                    'success': True
                }, status=status.HTTP_200_OK)
                
            # 3. Retornamos las órdenes serializadas
            serializer = self.get_serializer(orders, many=True)
            return Response({
                'message': 'Tus pedidos fueron obtenidos con éxito',
                'results': serializer.data,
                'success': True
            }, status=status.HTTP_200_OK)
            
        except Exception as ex:
            logger.critical(f'Error interno en get_my_orders: {ex}')
            return Response({
                'message': f'Hubo un error al cargar tus pedidos: {str(ex)}',
                'success': False
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

class OrdersDetailsViewSet(viewsets.GenericViewSet):
    queryset = OrdersDetail.objects.all()
    serializer_class = OrderDetailSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Pedidos'
    search_fields = ['id_detail','order','variant','quantity','sales_price','subtotal']

    @action(detail=False,methods=['GET'])
    def get_details(self, request):
        try:
            details = self.get_queryset()
            serializer = self.get_serializer(details,many=True)
            return Response({'message':'detalles obtenidos', 'results':serializer.data,'success':True},status=status.HTTP_200_OK)
        except ValueError as ve:
            logger.error(f'error de valores: {ve}', exc_info=True)
            return Response({'message':'error de valores','success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}', exc_info=True)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_details_by_id(self, request, pk=None):
        try:
            detail = self.get_object()
            serializer = self.get_serializer(detail,many=False)
            return Response({'message':'detalle obtenido','results':serializer.data,'success':True},status=status.HTTP_200_OK)
        except OrdersDetail.DoesNotExist as ne:
            logger.error(f'error de detalle: {ne}', exc_info=True)
            return Response({'message':'el detalle no existe','success':False},status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos devueltos: {mo}', exc_info=True)
            return Response({'message':'multiples objetos retornados','success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}', exc_info=True)
            return Response({'message':str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_details_by_order(self, request, pk=None):
        try:
            details = OrdersDetail.objects.filter(order=pk)
            if not details.exists():
                return Response({'message':'no se encontraron detalles','success':False},status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(details,many=True)
            return Response({'message':'detalles obtenidos','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except ValueError as ve:
            logger.error(f'erro de valor: {ve}', exc_info=True)
            return Response({'message':'error de valores','success':False},status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}', exc_info=True)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_details(self,request):
        try:
            queryset = self.get_queryset()
            if not queryset.exists():
                return Response({'message':'no hay detalles','success':False}, status=status.HTTP_400_BAD_REQUEST)
            instance = self.filter_queryset(queryset)
            serializer = self.get_serializer(instance,many=True)
            return Response({'message':'detalles encontrados','results':serializer.data,'success':True},status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}', exc_info=True)
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class PaymentMethodsViewSet(viewsets.ModelViewSet):
    queryset = PaymentMethods.objects.all()
    serializer_class = PaymentMethodsSerializer
    permission_classes = [permissions.AllowAny]
    required_module = 'Orders'

        
    

# Create your views here.

```

## ARCHIVO: .\api\Products\urls.py
```python
from rest_framework import routers
from django.urls import path,include
from .views import ProductsViewSets,ColorViewSets,SizesViewSets, ProductPhotosViewSets, VariantProductViewSets

router = routers.DefaultRouter()
router.register(r'products', ProductsViewSets, basename='products')
router.register(r'colors', ColorViewSets, basename='colors')
router.register(r'sizes', SizesViewSets, basename='sizes')
router.register(r'photos', ProductPhotosViewSets, basename='photos')
router.register(r'variants', VariantProductViewSets, basename='variants')

urlpatterns = [
    path('', include(router.urls))
]
# from. views
```

## ARCHIVO: .\api\Products\views.py
```python
from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status, viewsets, filters, permissions
from rest_framework.decorators import action
from django.core.exceptions import MultipleObjectsReturned
from django.db.utils import IntegrityError
from .models import Products, Sizes, Colors, ProductPhoto, VariantProduct
from .serializers import ProductsSerializer, PatchStateProductsSerializer, ColorsSerializer, SizesSerializer, ProductsPhotosSerializer, VariantProductsSerializer
from .services import create_inventory_for_variant, Export_products_list
from django.db import transaction
from api.Inventory.services import add_stock
import logging

logger = logging.getLogger(__name__)

class ProductsViewSets(viewsets.GenericViewSet):
    queryset = Products.objects.all()
    serializer_class = ProductsSerializer
    # authentication_classes = []
    permission_classes = [permissions.AllowAny]
    required_module = 'Productos'
    filter_backends = [filters.SearchFilter]
    search_fields = ['id_product','name','category','price','is_active']

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return PatchStateProductsSerializer
        return ProductsSerializer
    
    @action(detail=False,methods=['GET'])
    def get_products(self, request):
        try:
            products = self.get_queryset()
            serializer = self.get_serializer(products, many=True)
            print(serializer.data)
            return Response({'message':'productos obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,methods=['GET'])
    def get_products_by_id(self, request, pk=None):
        try:
            product = self.get_object()
            serialzier = self.get_serializer(product, many=False)
            print(serialzier.data)
            return Response({'message':'producto encontrado', 'results':serialzier.data, 'success':True}, status=status.HTTP_200_OK)
        except Products.DoesNotExist:
            return Response({'message':'producto no encontrada', 'results':[], 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'resutls':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False,methods=['POST'])
    @transaction.atomic
    def create_products(self, request):
        try:
            print(f'data enviada: {request.data}')
            data_product = request.data
            serializer_product = self.get_serializer(data=data_product)
            serializer_product.is_valid(raise_exception=True)
            product_instance = serializer_product.save()

            data_variant = request.data.copy()
            data_variant['product'] = product_instance.id_product

            serializer_variant = VariantProductsSerializer(data=data_variant)
            serializer_variant.is_valid(raise_exception=True)
            variant_instance = serializer_variant.save(product=product_instance)
            
            create_inventory_for_variant(variant=variant_instance)
            
            quantity = request.data.get('stock')

            try:
                quantity = int(quantity)
            except (TypeError, ValueError):
                quantity = 0
            if quantity > 0:
                add_stock(variant_instance, quantity)
        
            return Response({'message':'creado exitosamente', 'product':serializer_product.data, 'variant':serializer_variant.data, 'success':True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message':'error de lalves', 'results':[], 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            print('error de servidor:',ex)
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_products(self, request, pk=None):
        try:
            product = self.get_object()
            product.delete()
            return Response({'message':'elimiando exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}')
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_products(self, request, pk=None):
        try:
            product = self.get_object()
            serializer = self.get_serializer(product, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'actualizado exitosamente', 'product':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Products.DoesNotExist:
            return Response({'message':'este producto no existe', 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False,methods=['GET'])
    def search_products(self, request):
        try:
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset=queryset)
            serializer = self.get_serializer_class(instance, many=True)
            return Response({'message':'productos encontrados', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Products.DoesNotExist:
            return Response({'message':'no se encontraron productos', 'results':[], 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PATCH'])
    def patch_state(self, request, pk=None):
        try:
            product = self.get_object()
            serializer = self.get_serializer(product, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            print(f'data: {request.data}')
            return Response({'message':'estado actualizado exitosamente', 'product':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Products.DoesNotExist:
            return Response({'message':'este producto no existe', 'results':[], 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'message':'error de llaves', 'results':[], 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}, data: {serializer.data}')
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def export_products(self, request):
        try:
            queryset = self.get_queryset().select_related('category').prefetch_related('variants','variants__size','variants__color')

            list = Export_products_list(queryset)

            return list
        except Exception as ex:
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ColorViewSets(viewsets.GenericViewSet):
    queryset = Colors.objects.all()
    serializer_class = ColorsSerializer
    required_module = 'Productos'
    permission_classes = [permissions.AllowAny]
    # authentication_classes = []

    @action(detail=False,methods=['GET'])
    def get_colors(self, request):
        try:
            colors = self.get_queryset()
            serializer = self.get_serializer(colors,many=True)
            return Response({'message':'colores obtenidos exitosamente', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_colors_by_id(self, request, pk=None):
        try:
            color = self.get_object()
            serializer = self.get_serializer(color,many=False)
            return Response({'message':'color obtenido','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','results':[],'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_colors(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'color creado exitosamente','object':serializer.data,'success':True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message':'error de llaves','success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_color(self, request, pk=None):
        try:
            color = self.get_object()
            color.delete()
            return Response({'message':'eliminado exitosamente','success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Colors.DoesNotExist:
            return Response({'message':'este color no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_color(self, request, pk=None):
        try:
            color = self.get_object()
            serializer = self.get_serializer(color, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'color actualizado exitosamente', 'color':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetso retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Colors.DoesNotExist:
            return Response({'message':'este color no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class SizesViewSets(viewsets.GenericViewSet):
    queryset = Sizes.objects.all()
    serializer_class = SizesSerializer
    required_module = 'Productos'
    permission_classes = [permissions.AllowAny]
    # authentication_classes = []

    @action(detail=False,methods=['GET'])
    def get_sizes(self, request):
        try:
            sizes = self.get_queryset()
            serializer = self.get_serializer(sizes, many=True)
            return Response({'message':'tallas obtenidas', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_sizes_by_id(self, request, pk=None):
        try:
            size = self.get_object()
            serializer = self.get_serializer(size,many=False)
            return Response({'message':'talla obtenida', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return  Response({'message':'multiples objetos retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_sizes(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'talla creada exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message':'error de llaves', 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_sizes(self, request, pk=None):
        try:
            size = self.get_object()
            size.delete()
            return Response({'message':'eliminado exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Sizes.DoesNotExist:
            return Response({'message':'esta talla no existe', 'results':[], 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_sizes(self, request, pk=None):
        try:
            size = self.get_object()
            serializer = self.get_serializer(size, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'talla actualizada exitosamente','size':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Sizes.DoesNotExist:
            return Response({'message':'esta talla no existe', 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ProductPhotosViewSets(viewsets.GenericViewSet):
    queryset = ProductPhoto.objects.all()
    serializer_class = ProductsPhotosSerializer
    permission_classes = [permissions.AllowAny]
    # authentication_classes = []

    @action(detail=False,methods=['GET'])
    def get_photos(self, request):
        try:
            photos = self.get_queryset()
            serializer = self.get_serializer(photos,many=True)
            return Response({'message':'fotos obtenidas', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            print(f'error: {ex}')
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_photos_by_id(self, request, pk=None):
        try:
            photo = self.get_object()
            serializer = self.get_serializer(photo,many=False)
            return Response({'message':'foto obtenida', 'results':serializer.data, 'success':False}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_photos(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'photo agregada exitosamente', 'object':serializer.data, 'success':False}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message':'error de llaves', 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            print(f'error: {ex}')
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_photos(self, request, pk=None):
        try:
            photo = self.get_object()
            photo.delete()
            return Response({'message':'foto eliminada exitosamente', 'success':False}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ProductPhoto.DoesNotExist:
            return Response({'message':'esta foto no existe', 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class VariantProductViewSets(viewsets.GenericViewSet):
    queryset = VariantProduct.objects.all()
    serializer_class = VariantProductsSerializer    
    required_module = 'Productos'
    permission_classes = [permissions.AllowAny]
    # authentication_classes = []

    @action(detail=False,methods=['GET'])
    def get_variants(self, request):
            variants = self.get_queryset()
            serializer = self.get_serializer(variants,many=True)
            return Response({'message':'variantes obtenidas exitosamente','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
    
    @action(detail=True,methods=['GET'])
    def get_variants_by_id(self, request, pk=None):
        try:
            variant = self.get_object()
            serializer = self.get_serializer(variant,many=False)
            return Response({'message':'variante obtenida','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','results':[],'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def create_variant(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            print(f'data a serializer: {request.data}')
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'creado exitosamente', 'results':serializer.data,'success':True}, status=status.HTTP_201_CREATED)
        except Exception as ex:
            print(f'error {ex}')
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_variant(self, request, pk=None):
        try:
            variant = self.get_object()
            variant.delete()
            return Response({'message':'variante eliminada exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        
        
    
        



        
        
# Create your views here.

```

## ARCHIVO: .\api\Providers\urls.py
```python
from django.urls import  path,include
from rest_framework import routers
from .views import ProvidersViewSets

router = routers.DefaultRouter()
router.register(r'providers', ProvidersViewSets, basename='providers')

urlpatterns = [
    path('', include(router.urls))
]
```

## ARCHIVO: .\api\Providers\views.py
```python
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

        

        


# Create your views here.

```

## ARCHIVO: .\api\Purchases\urls.py
```python
from rest_framework import routers
from .views import PurchasesViewSet, PurchaseDetailViewSet, IvaViewSets
from django.urls import path,include

router = routers.DefaultRouter()
router.register(r'purchases',PurchasesViewSet,basename='purchases')
router.register(r'purchasesdetails', PurchaseDetailViewSet, basename='purchasesdetails')
router.register(r'iva', IvaViewSets, basename='iva')

urlpatterns = [
    path('', include(router.urls))
]
```

## ARCHIVO: .\api\Purchases\views.py
```python
from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Purchases, PurchaseDetail, Iva
from .serializers import PurchasesSerializer, PurchaseDetailSerializer, IvaSerializer
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from api.Inventory.services import out_stock
from api.States.models import States
from .services import Export_purchases_list

class PurchasesViewSet(viewsets.GenericViewSet):
    queryset = Purchases.objects.all()
    serializer_class = PurchasesSerializer
    required_module = 'Compras'
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'purchase_number',
        'provider__name',
        'state__name',
        'observations',
        'total',
        'subtotal',
        'iva',
    ]

    @action(detail=False, methods=['GET'])
    def get_purchases(self, request):
        try:
            purchases = self.get_queryset()
            if not purchases.exists():
                return Response({'results': [], 'success': True}, status=status.HTTP_200_OK)
            serializer = self.get_serializer(purchases, many=True)
            return Response({'message': 'compras obtenidas', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            print(f'error: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['GET'])
    def get_purchase_by_id(self, request, pk=None):
        try:
            purchase = self.get_object()
            serializer = self.get_serializer(purchase)
            return Response({'message': 'compra obtenida', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Purchases.DoesNotExist:
            return Response({'message': 'compra no encontrada', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    def create_purchase(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            if not serializer.is_valid():
                print(f'error de validacion: {serializer.errors}')
            print(f'data: {request.data}')
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message': 'compra creada exitosamente', 'object': serializer.data, 'success': True}, status=status.HTTP_201_CREATED)
        except IntegrityError as ie:
            print(f'error de datos: {ie}')
            return Response({'message': 'error de integridad en los datos', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            print(f'error: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['PUT'])
    def update_purchase(self, request, pk=None):
        try:
            purchase = self.get_object()
            serializer = self.get_serializer(purchase, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message': 'compra actualizada exitosamente', 'object': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Purchases.DoesNotExist:
            return Response({'message': 'compra no encontrada', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['PATCH'])
    def patch_state(self, request, pk=None):
        try:
            purchase = self.get_object()

            is_canceled = request.data.get('canceled')

            is_canceled_bool = str(is_canceled).lower() in ['true', '1']

            purchase.canceled = is_canceled_bool

            purchase.save()
            serializer = self.get_serializer(purchase)
            return Response({'message': 'estado actualizado', 'object': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Purchases.DoesNotExist:
            return Response({'message': 'compra no encontrada', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            print('error de servidor:',ex)
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def get_purchase_by_provider(self, request):
        try:
            provider = request.query_params['provider']
            purchases = Purchases.objects.filter(provider=provider)
            serializer = self.get_serializer(purchases, many=True)
            return Response({'message':'compras obtenidas','results':serializer.data,'success':False},status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error de servidor':str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR) 
            

    @action(detail=True, methods=['DELETE'])
    def delete_purchase(self, request, pk=None):
        try:
            purchase = self.get_object()

            is_canceled = purchase.canceled
            if is_canceled != True:
                return Response({'message': f'Solo se pueden eliminar compras anuladas','success': False}, status=status.HTTP_400_BAD_REQUEST)

            for detail in purchase.detail_purchase.all():
                out_stock(detail.variant, detail.quantity)

            purchase.delete()
            return Response({'message': 'compra eliminada exitosamente', 'success': True}, status=status.HTTP_200_OK)
        except Purchases.DoesNotExist:
            return Response({'message': 'compra no encontrada', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'message': 'error de integridad', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            print('error de servidor:',ex)
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_purchases(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            if not queryset.exists():
                return Response({'message': 'sin resultados', 'results': [], 'success': False}, status=status.HTTP_200_OK)
            serializer = self.get_serializer(queryset, many=True)
            return Response({'message': 'resultados obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def export_purchases(self, request):
        try:
            queryset = self.get_queryset().select_related('provider','state').prefetch_related('detail_purchase__variant__product')

            list = Export_purchases_list(queryset)
            return list
        except Exception as ex:
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class PurchaseDetailViewSet(viewsets.GenericViewSet):
    queryset = PurchaseDetail.objects.all()
    serializer_class = PurchaseDetailSerializer
    required_module = 'Compras'
    filter_backends = [filters.SearchFilter]
    search_fields = [
        'purchase__purchase_number',
        'variant__sku',
        'variant__product__name',
        'quantity',
        'purchase_price',
        'sales_price',
        'subtotal',
    ]

    @action(detail=False, methods=['GET'])
    def get_details(self, request):
        try:
            details = self.get_queryset()
            if not details.exists():
                return Response({'results': [], 'success': True}, status=status.HTTP_200_OK)
            serializer = self.get_serializer(details, many=True)
            return Response({'message': 'detalles obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['GET'])
    def get_detail_by_id(self, request, pk=None):
        try:
            detail = self.get_object()
            serializer = self.get_serializer(detail)
            return Response({'message': 'detalle obtenido', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except PurchaseDetail.DoesNotExist:
            return Response({'message': 'detalle no encontrado', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ─── GET detalles por compra ──────────────────────────────────────────────
    @action(detail=True, methods=['GET'])
    def get_details_by_purchase(self, request, pk=None):
        try:
            details = PurchaseDetail.objects.filter(purchase=pk)
            if not details.exists():
                return Response({'message': 'esta compra no tiene detalles', 'results': [], 'success': True}, status=status.HTTP_200_OK)
            serializer = self.get_serializer(details, many=True)
            return Response({'message': 'detalles obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_details(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            if not queryset.exists():
                return Response({'message': 'sin resultados', 'results': [], 'success': False}, status=status.HTTP_200_OK)
            serializer = self.get_serializer(queryset, many=True)
            return Response({'message': 'resultados obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
class IvaViewSets(viewsets.ModelViewSet):
    required_module = 'Compras'
    queryset = Iva.objects.all()
    serializer_class = IvaSerializer
```

## ARCHIVO: .\api\Returns\urls.py
```python
from rest_framework import routers
from .views import ReturnsViewSets, ReturnDetailViewsets, ChangesViewSets, ChangesDetailViewsets
from django.urls import path, include

router = routers.DefaultRouter()

router.register(r'returns', ReturnsViewSets, basename='returns')
router.register(r'returnsdetail', ReturnDetailViewsets, basename='returndetail')
router.register(r'changes', ChangesViewSets, basename='changes')
router.register(r'changesdetail', ChangesDetailViewsets, basename='changesdetail')

urlpatterns = [
    path('', include(router.urls))
]
```

## ARCHIVO: .\api\Returns\views.py
```python
from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Returns, ReturnDetail, Changes, ChangesDetails
from .serializers import ReturnsSerializer, ReturnDetailSerializer, ChangesSerializer, ChangesDetailsSerializer
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from api.Inventory.services import add_stock
from .services import Export_returns_list
from django.http import HttpResponse
import logging
from django.db import transaction

logger = logging.getLogger(__name__)


# ==================== VIEWSETS PARA DEVOLUCIONES ====================

class ReturnsViewSets(viewsets.GenericViewSet):
    queryset = Returns.objects.all()
    serializer_class = ReturnsSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Devoluciones'
    search_fields = ['id_return', 'return_number', 'sale', 'return_date', 'reason', 'state', 'total', 'balance_in_favor', 'difference_to_pay']

    @action(methods=['GET'], detail=False)
    def get_returns(self, request):
        try:
            returns = self.get_queryset()
            if not returns.exists():
                logger.warning(f'no se encontraron devoluciones')
                return Response({'message': 'no existen devoluciones', 'success': False}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(returns, many=True)
            return Response({'message': 'devoluciones obtenidas', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'ocurrio un error de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['GET'], detail=True)
    def get_return_by_id(self, request, pk=None):
        try:
            return_obj = self.get_object()
            serializer = self.get_serializer(return_obj, many=False)
            logger.info(f'devolución obtenida: {serializer.data}')
            return Response({'message': 'devolución obtenida', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Returns.DoesNotExist as ne:
            logger.warning(f'la devolución no existe: {ne}')
            return Response({'message': 'Esta devolución no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiple objetos retornados: {mo}')
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    @transaction.atomic
    def create_return(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f'devolución creada exitosamente')
            return Response({'message': 'devolución creada exitosamente', 'success': True}, status=status.HTTP_201_CREATED)
        except IntegrityError as ie:
            logger.critical(f'error de integridad en base de datos: {ie}')
            return Response({'message': 'Error de integridad en los datos', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['DELETE'])
    @transaction.atomic
    def delete_return(self, request, pk=None):
        try:
            return_obj = self.get_object()
            current_state = return_obj.state.name_state

            if current_state != 'Anulado':
                return Response({'message': f'Solo se pueden eliminar devoluciones anuladas', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

            # Revertir stock para todos los detalles de la devolución
            for detail in return_obj.return_detail.all():
                add_stock(detail.variant, detail.quantity)
                logger.info(f'stock revertido para variante: {detail.variant.id}, cantidad: {detail.quantity}')

            return_obj.delete()
            logger.info(f'devolución eliminada exitosamente')
            return Response({'message': 'devolución eliminada exitosamente', 'success': True}, status=status.HTTP_200_OK)
        except Returns.DoesNotExist as de:
            logger.warning(f'esta devolución no esta disponible: {de}')
            return Response({'message': 'esta devolución no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos devueltos por el servidor: {mo}')
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_returns(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response({'message': 'devoluciones obtenidas', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_metrics(self, request):
        try:
            cantidad_devoluciones = Returns.objects.count()
            logger.info(f'métricas de devoluciones obtenidas')
            return Response({
                'message': 'métricas de devoluciones',
                'metrics': {
                    'cantidad_devoluciones': cantidad_devoluciones
                },
                'success': True
            }, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error al obtener métricas: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def export_all_returns(self, request):
        try:
            queryset = Returns.objects.select_related('sale', 'state').prefetch_related('return_detail__variant__product')
            file = Export_returns_list(queryset)
            return file
        except Exception as ex:
            logger.critical(f'error al exportar devoluciones: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['GET'])
    def export_return_by_id(self, request, pk=None):
        try:
            return_obj = self.get_object()
            queryset = Returns.objects.filter(id_return=pk).select_related('sale', 'state').prefetch_related('return_detail__variant__product')
            file = Export_returns_list(queryset)
            return file
        except Returns.DoesNotExist as de:
            logger.warning(f'devolución no encontrada para exportar: {de}')
            return Response({'message': 'esta devolución no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            logger.critical(f'error al exportar devolución: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ReturnDetailViewsets(viewsets.ModelViewSet):
    queryset = ReturnDetail.objects.all()
    serializer_class = ReturnDetailSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Devoluciones'
    search_fields = ['return_id', 'variant', 'quantity', 'subtotal']

    @action(detail=True, methods=['GET'])
    def get_returns_by_id(self, request, pk=None):
        try:
            details = ReturnDetail.objects.filter(return_id=pk)
            if not details.exists():
                logger.warning(f'no se encontraron detalles en la devolución')
                return Response({'message': 'no hay detalles en esta devolución', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(details, many=True)
            return Response({'message': 'detalle de la devolución', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_details(self, request):
        try:
            instances = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(instances, many=True)
            return Response({'message': 'detalles encontrados', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==================== VIEWSETS PARA CAMBIOS ====================

class ChangesViewSets(viewsets.GenericViewSet):
    queryset = Changes.objects.all()
    serializer_class = ChangesSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Devoluciones'
    search_fields = ['id_change', 'change_number', 'sale', 'reason_of_change', 'state', 'stock_applied', 'return_applied']

    @action(methods=['GET'], detail=False)
    def get_changes(self, request):
        try:
            changes = self.get_queryset()
            if not changes.exists():
                logger.warning(f'no se encontraron cambios')
                return Response({'message': 'no existen cambios', 'success': False}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(changes, many=True)
            return Response({'message': 'cambios obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'ocurrio un error de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(methods=['GET'], detail=True)
    def get_change_by_id(self, request, pk=None):
        try:
            change_obj = self.get_object()
            serializer = self.get_serializer(change_obj, many=False)
            logger.info(f'cambio obtenido: {serializer.data}')
            return Response({'message': 'cambio obtenido', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Changes.DoesNotExist as ne:
            logger.warning(f'el cambio no existe: {ne}')
            return Response({'message': 'Este cambio no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiple objetos retornados: {mo}')
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['POST'])
    @transaction.atomic
    def create_change(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            logger.info(f'cambio creado exitosamente')
            return Response({'message': 'cambio creado exitosamente', 'success': True}, status=status.HTTP_201_CREATED)
        except IntegrityError as ie:
            logger.critical(f'error de integridad en base de datos: {ie}')
            return Response({'message': 'Error de integridad en los datos', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['DELETE'])
    @transaction.atomic
    def delete_change(self, request, pk=None):
        try:
            change_obj = self.get_object()
            current_state = change_obj.state.name_state

            if current_state != 'Anulado':
                return Response({'message': f'Solo se pueden eliminar cambios anulados', 'success': False}, status=status.HTTP_400_BAD_REQUEST)

            # Revertir stock para todos los detalles del cambio si aplica
            if change_obj.stock_applied:
                for detail in change_obj.change_detail.all():
                    # Devolver el stock de la variante entregada
                    add_stock(detail.variant_delivered, 1)
                    logger.info(f'stock revertido para variante entregada: {detail.variant_delivered.id}')

            change_obj.delete()
            logger.info(f'cambio eliminado exitosamente')
            return Response({'message': 'cambio eliminado exitosamente', 'success': True}, status=status.HTTP_200_OK)
        except Changes.DoesNotExist as de:
            logger.warning(f'este cambio no esta disponible: {de}')
            return Response({'message': 'este cambio no existe', 'success': False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos devueltos por el servidor: {mo}')
            return Response({'message': 'multiples objetos retornados', 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_changes(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response({'message': 'cambios obtenidos', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def get_metrics(self, request):
        try:
            cantidad_cambios = Changes.objects.count()
            logger.info(f'métricas de cambios obtenidas')
            return Response({
                'message': 'métricas de cambios',
                'metrics': {
                    'cantidad_cambios': cantidad_cambios
                },
                'success': True
            }, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error al obtener métricas: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class ChangesDetailViewsets(viewsets.ModelViewSet):
    queryset = ChangesDetails.objects.all()
    serializer_class = ChangesDetailsSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Devoluciones'
    search_fields = ['change', 'variant_returned', 'variant_delivered']

    @action(detail=True, methods=['GET'])
    def get_changes_by_id(self, request, pk=None):
        try:
            details = ChangesDetails.objects.filter(change=pk)
            if not details.exists():
                logger.warning(f'no se encontraron detalles en el cambio')
                return Response({'message': 'no hay detalles en este cambio', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(details, many=True)
            return Response({'message': 'detalle del cambio', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['GET'])
    def search_details(self, request):
        try:
            instances = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(instances, many=True)
            return Response({'message': 'detalles encontrados', 'results': serializer.data, 'success': True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex), 'success': False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# Create your views here.

```

## ARCHIVO: .\api\Roles\urls.py
```python
from django.urls import path, include
from .views import RolesViewSets, PermissionsViewSets, RolPermissionViewSets
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'roles', RolesViewSets, basename='roles')
router.register(r'permissions', PermissionsViewSets, basename='permissions')
router.register(r'rolPermission', RolPermissionViewSets, basename='rolPermission')

urlpatterns = [
    path('', include(router.urls))
]
```

## ARCHIVO: .\api\Roles\views.py
```python
from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Roles, Permissions, RolPermission
from .serializers import RolesSerializers, PermissionsSerializer, PatchStateRolesSerializer, RolPermissionSerializer
from rest_framework.exceptions import APIException, ValidationError
from api.Exceptions.exceptions import ObjectNotExists,MultiResults, IntegrityException, InvalidData
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned

class RolesViewSets(viewsets.GenericViewSet):
    queryset = Roles.objects.all()
    serializer_class = RolesSerializers
    required_module = 'Roles'
    # permission_classes = []
    # authentication_classes = []
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']

    def get_serializer_class(self):
        if self.action == 'change_state':
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
        except ValidationError as e:
            print('error', e.detail)
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
            return Response({'results':'eliminado exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except Roles.DoesNotExist:
            raise ObjectNotExists()
        except IntegrityError:
            raise IntegrityException()
        except Exception as ex:
            print('error de servidor:',ex)
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
            rol = self.get_object()
            serializer = self.get_serializer(rol, data=request.data, partial=True)
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

    @action(detail=False,methods=['GET'])
    def get_all_permissions(self, request):
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
        
class RolPermissionViewSets(viewsets.GenericViewSet):
    queryset = RolPermission.objects.all()
    serializer_class = RolPermissionSerializer
    # authentication_classes = []
    # permission_classes = []
        
    @action(detail=False,methods=['POST'])
    def assing_permission(self, request):
            serializer = self.get_serializer(data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'permiso asignado correctamente', 'success':True}, status=status.HTTP_200_OK)
    
    @action(detail=False,methods=['DELETE'])
    def delete_rol_permission(self, request):
        rol_id = request.data.get('rol')
        permission_id = request.data.get('permission')
        if not rol_id or not permission_id:
            return Response({'message':'debes enviar rol y permiso', 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        
        delete_camp = RolPermission.objects.filter(rol=rol_id, permission=permission_id)
        delete_camp.delete()
        return Response({'message':'eliminado exitosamente', 'success':True}, status=status.HTTP_200_OK)
    
    @action(detail=True,methods=['GET'])
    def get_permissions_by_rol(self, request, pk=None):

        if not Roles.objects.filter(idRol=pk).exists():
                return Response(
                    {'message': 'El rol especificado no existe', 'results': [], 'success': False},
                    status=status.HTTP_404_NOT_FOUND
                )
        print(f'id del rol: {pk}')

        rol_permission = RolPermission.objects.filter(rol_id=pk).select_related('permission')
        print(f'permisos: {rol_permission}')
        if not rol_permission.exists():
            return Response(
                {'message': 'Este rol no tiene permisos asignados', 'results': [], 'success': True},
                status=status.HTTP_200_OK
            )
        serializer = self.get_serializer(rol_permission, many=True)
        return Response({'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
# Create your views here.

```

## ARCHIVO: .\api\Sales\urls.py
```python
from rest_framework import routers
from django.urls import path,include
from .views import SalesDetailViewsets,SalesViewSets

router = routers.DefaultRouter()

router.register(r'sales', SalesViewSets, basename='sales')
router.register(r'salesdetails', SalesDetailViewsets, basename='salesdetails')

urlpatterns = [
    path('', include(router.urls))
]
```

## ARCHIVO: .\api\Sales\views.py
```python
from django.shortcuts import render
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Sales, SalesDetail
from .serializers import SalesSerializer, SalesDetailsSerializer
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from api.Inventory.services import add_stock
from .services import Export_sales_list
import logging
from django.db import transaction

logger = logging.getLogger(__name__)

class SalesViewSets(viewsets.GenericViewSet):
    queryset = Sales.objects.all()
    serializer_class = SalesSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Ventas'
    search_fields = ['id_sale','number_sale','client','date_sale','state','payment_method','subtotal','iva',
    'total','output_executing','return_executing','void','void_reason']

    @action(methods=['GET'],detail=False)
    def get_sales(self, request):
        try:    
            sales = self.get_queryset()
            if not sales:
                logger.warning(f'no se encontraron ventas')
                return Response({'message':'no existen ventas','success':False}, status=status.HTTP_404_NOT_FOUND)
            serializer = self.get_serializer(sales,many=True)
            return Response({'message':'ventas obtenidas','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'ocurrio un error de servidor: {ex}')
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    
    @action(methods=['GET'],detail=True)
    def get_sales_by_id(self, request, pk=None):
        try:
            sale = self.get_object()
            serializer = self.get_serializer(sale,many=False)
            logger.info(f'venta obtenida: {serializer.data}')
            return Response({'message':'venta obtenida','results':serializer.data,'success':True},status=status.HTTP_200_OK)
        except Sales.DoesNotExist as ne:
            logger.warning(f'la venta no existe: {ne}')
            return Response({'message':'Esta venta no existe', 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiple objetos retornados:{mo}')
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno de servidor: {ex}')
            return Response({'message':str(ex), 'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_sale(self, request):
        try:
            serializer = self.get_serializer(data=request.data)
            print(f'data: {request.data}')
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'venta creada exitosamente', 'success':True}, status=status.HTTP_201_CREATED)
        except Exception as ex:
            logger.critical(f'error de servidor: {ex}')
            return Response({'message':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,methods=['DELETE'])
    @transaction.atomic  
    def delete_sale(self, request, pk=None):
        try:
            sale = self.get_object()
            current_state = sale.state.name_state

            if current_state != 'Anulado':
                return Response({'message': f'Solo se pueden eliminar compras anuladas', 'success': False}, status=status.HTTP_400_BAD_REQUEST)
            
            for detail in sale.sales_details.all():
                add_stock(detail.variant, detail.quantity)

            sale.delete()
            return Response({'message':'venta eliminada exitosamente','success':True}, status=status.HTTP_200_OK)
        except Sales.DoesNotExist as de:
            logger.warning(f'esta venta no esta disponible: {de}')
            return Response({'message':'esta venta no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos devueltos por el servidor: {mo}')
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_sales(self, request, pk=None):
        try:
            sale = self.get_object()
            serializer = self.get_serializer(sale, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'venta actualizada exitosamente','object':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Sales.DoesNotExist as de:
            logger.warning(f'esta venta no existe: {de}')
            return Response({'message':'esta venta no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos retornados por el servidor: {mo}')
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'ocurrio un error interno de servidor: {ex}')
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_sales(self, request):
        try:
            queryset = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(queryset, many=True)
            return Response({'message':'ventas obtenidas','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message': str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PATCH'])
    def patch_state(self, request, pk=None):
        try:
            sale = self.get_object()

            current_state = sale.state.name_state
            if current_state in ['entregada','anulada','cancelada']:
                return Response({'message':f'no se puede cambiar la venta con estado: {current_state}','success':False}, status=status.HTTP_400_BAD_REQUEST)
            
            state_id = request.data.get('state')
            if not state_id:
                return Response({'message':'necesitas enviar un estado','success':False}, status=status.HTTP_400_BAD_REQUEST)
            
            sale.state_id_state = state_id
            sale.save()
            serializer = self.get_serializer(sale)
            return Response({'message':'estado actualizado exitosamente','object':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned as mo:
            logger.critical(f'multiples objetos retornados por el servidor: {mo}')
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            logger.critical(f'error interno de servidor: {ex}')
            return  Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def export_sales(self, request):
        try:
            queryset = Sales.objects.select_related('client','state').prefetch_related('sale_detail__variant__product')
            list = Export_sales_list(queryset)

            return list
        except Exception as ex:
            return Response({'message':str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class SalesDetailViewsets(viewsets.ModelViewSet):
    queryset = SalesDetail.objects.all()
    serializer_class = SalesDetailsSerializer
    filter_backends = [filters.SearchFilter]
    required_module = 'Ventas'
    search_fields = ['sale' , 'variant' ,'quantity' ,'unit_price' ,'subtotal' ,'creation_date',]

    @action(detail=True,methods=['GET'])
    def get_sales_by_id(self, request, pk=None):
        try:
            details = SalesDetail.objects.filter(sale=pk)
            if not details.exists():
                logger.warning(f'no se encontraron detaller en la compra')
                return Response({'message':'no hay detalles en esta venta','success':False},status=status.HTTP_400_BAD_REQUEST)
            serializer = self.get_serializer(details,many=True)
            return Response({'message':'detalle de la venta','results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor: {ex}')
            return Response({'message':str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['GET'])
    def search_details(self, request):
        try:
            instances = self.filter_queryset(self.get_queryset())
            serializer = self.get_serializer(instances, many=True)
            return Response({'message':'detalles encontrados','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            logger.critical(f'error interno del servidor:{ex}')
            return Response({'message':str(ex),'success':False},status=status.HTTP_500_INTERNAL_SERVER_ERROR)


        

    

            


        

    
# Create your views here.

```

## ARCHIVO: .\api\States\urls.py
```python
from rest_framework import routers
from .views import StatesViewSets
from django.urls import path,include

router = routers.DefaultRouter()
router.register(r'states', StatesViewSets, basename='states')

urlpatterns = [
    path('', include(router.urls))
]
```

## ARCHIVO: .\api\States\views.py
```python
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

```

## ARCHIVO: .\api\Users\urls.py
```python
from rest_framework import routers
from django.urls import path,include
from .views import UsersViewSets, TypesDocsViewSets,LoginView, ChangePasswordView, RequestOTPView, ValidateOTPView, ResetPasswordView, ClientsViewSets
from rest_framework_simplejwt.views import TokenRefreshView

router = routers.DefaultRouter()

router.register(r'users', UsersViewSets, basename='users')
router.register(r'typesDocs', TypesDocsViewSets, basename='typesDocs')
router.register(r'clients', ClientsViewSets, basename='clients')

urlpatterns =[
    path('', include(router.urls)),
    path('auth/login/',   LoginView.as_view(),       name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/change-password/',  ChangePasswordView.as_view(), name='change_password'),
    path('auth/request-otp/',      RequestOTPView.as_view(),     name='request_otp'),
    path('auth/validate-otp/',     ValidateOTPView.as_view(),    name='validate_otp'),
    path('auth/reset-password/',   ResetPasswordView.as_view(),  name='reset_password'),
]
```

## ARCHIVO: .\api\Users\views.py
```python
from django.shortcuts import render
from rest_framework import filters,status,viewsets, views, permissions
from rest_framework.response import Response
from .models import Users, Typesdoc, Clients
from .serializers import UsersSerializer, UsersPatchActiveSerializer, TypesDocsSerializers,LoginSerializer, ChangePasswordSerializer, RequestOTPSerializer,ValidateOTPSerializer, ResetPasswordSerializer, ClientsSerializers, StateSerializer
from rest_framework.decorators import action
from django.core.exceptions import MultipleObjectsReturned
from django.db.utils import IntegrityError
from rest_framework.exceptions import ValidationError, APIException
from api.Exceptions.exceptions import ObjectNotExists,MultiResults, IntegrityException, InvalidData
from .Services.ExportUsers import Export_users_list
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from drf_yasg.utils import swagger_auto_schema
from drf_yasg import openapi
from django.core.mail import send_mail
from django.db import transaction


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
    required_module = 'Usuarios'
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
    @transaction.atomic()    
    def create_users(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()

            return Response({'results':'creado exitosamente','user':serializer.data,'success':True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            raise IntegrityException()
        except MultipleObjectsReturned:
            raise MultiResults()
        except Exception as ex:
            print("error en servidor:",ex)
            raise APIException(detail=str(ex), code="error de servidor")
        
    @action(detail=True, methods=['DELETE'])
    def delete_users(self, request, pk=None):
        try:
            user = self.get_object()        
            user.delete()
            return Response({'results':'eliminado exitosamente', 'success':True}, status=status.HTTP_200_OK)
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
        
class ClientsViewSets(viewsets.GenericViewSet):
    queryset = Clients.objects.all()
    serializer_class = ClientsSerializers
    permission_classes = [permissions.IsAuthenticated]
    # authentication_classes = []
    required_module = 'Clientes'
    filter_backends = [filters.SearchFilter]
    search_fields = ['id_client','name','type_doc','doc','phone','address','email','state','city']

    def get_serializer_class(self):
        if self.action == 'patch_state':
            return StateSerializer
        return ClientsSerializers
    
    @action(detail=False,methods=['GET'])
    def get_clients(self, request):
        # print('AUTH HEADER:', request.headers.get('Authorization'))
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
        try:
            data_client = request.data
            client_serializer = self.get_serializer(data=data_client)
            client_serializer.is_valid(raise_exception=True)
            client_instance = client_serializer.save(user=request.user)
            return Response({'message':'creado exitosamente','results':client_instance.data,'success':True}, status=status.HTTP_201_CREATED)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

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
    
    @action(detail=False,methods=['GET'])
    def get_clients_by_rol(self, request, pk=None):
        try:
            rol = ['cliente','Cliente','Clientes','Cliente']
            users = Users.objects.filter(id_rol__name__icontains='clientes')
            if users.exists():
                serializer = UsersSerializer(users, many=True)
                return Response({'message':'clientes obtenidos','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
            else:
                print(f'clientes : {users}')
                return Response({'message':'no se encontraron clientes','success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            print(f'error: {ex}')
            return Response({'message':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        

# Create your views here.

        
         


# Create your views here.

```

## ARCHIVO: .\damabellaBackEnd\urls.py
```python
"""
URL configuration for damabellaBackEnd project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from rest_framework import permissions
from drf_yasg.views import get_schema_view
from drf_yasg import openapi
# from api.Users.views import LoginView
from rest_framework_simplejwt.views import TokenRefreshView

schema_view = get_schema_view(
    openapi.Info(
        title='Esquema documentacion, API damabella',
        default_version='v1',
        description='Documentacion completa de API desarrollada para el proyecto Damabella'
    ),
    public=True,
    permission_classes=(permissions.AllowAny,)
)



urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('api.urls')),
    path('Documentation/', schema_view.with_ui('swagger', cache_timeout=0), name='swagger-ui'),
    path('api/schemas/', schema_view.with_ui('redoc', cache_timeout=0), name='redoc'),
    # path('auth/login', LoginView.as_view(), name='login'),
    # path('auth/refresh', TokenRefreshView.as_view(), name='token_refresh')
]

```

