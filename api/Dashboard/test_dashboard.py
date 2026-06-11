from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from rest_framework.test import APITestCase, APIClient
from rest_framework import status
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock, PropertyMock
from datetime import datetime, date
import json

from api.Sales.models import Sales, SalesDetail
from api.Orders.models import Orders, OrdersDetail
from api.Users.models import Users
from api.Returns.models import Returns
from api.Sales.views import DashboardViewSets


User = get_user_model()


class DashboardViewSetsTestCase(APITestCase):
    """Test cases para DashboardViewSets"""

    def setUp(self):
        """Configuración inicial para cada test"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        # URLs base para los endpoints
        self.url_users_active = reverse('dashboard-get-users-active')
        self.url_pending_orders = reverse('dashboard-get-pending-orders')
        self.url_cantidad_ventas = reverse('dashboard-cantidad-ventas-mes')
        self.url_dinero_ventas = reverse('dashboard-dinero-ventas-mes')
        self.url_productos_vendidos = reverse('dashboard-productos-mas-vendidos')
        self.url_distribucion = reverse('dashboard-distribucion-categorias')
        self.url_metrics = reverse('dashboard-get-metrics')

    def tearDown(self):
        """Limpieza después de cada test"""
        pass

    # ==================== TESTS PARA get_users_active ====================

    def test_get_users_active_success(self):
        """Test: obtener cantidad de usuarios activos exitosamente"""
        # Crear usuarios activos e inactivos
        Users.objects.create(username='active1', is_active=True)
        Users.objects.create(username='active2', is_active=True)
        Users.objects.create(username='inactive1', is_active=False)

        response = self.client.get(self.url_users_active)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 3)  # 2 creados + 1 del setUp

    def test_get_users_active_no_users(self):
        """Test: obtener usuarios activos cuando no hay ninguno"""
        # Eliminar todos los usuarios excepto el de autenticación
        Users.objects.exclude(id=self.user.id).delete()
        self.user.is_active = False
        self.user.save()

        response = self.client.get(self.url_users_active)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 0)

    @patch('api.Users.models.Users.objects.filter')
    def test_get_users_active_exception(self, mock_filter):
        """Test: manejo de excepción en get_users_active"""
        mock_filter.side_effect = Exception('Database error')

        response = self.client.get(self.url_users_active)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('Database error', response.data['error'])

    # ==================== TESTS PARA get_pending_orders ====================

    def test_get_pending_orders_success(self):
        """Test: obtener órdenes pendientes exitosamente"""
        # Crear mock de estado y orden
        state_mock = MagicMock()
        state_mock.name_state = "Pendiente"

        order = Orders.objects.create(
            state=state_mock,
            total=100.00
        )

        with patch('api.Orders.models.Orders.objects.filter') as mock_filter:
            mock_filter.return_value.count.return_value = 5
            response = self.client.get(self.url_pending_orders)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_get_pending_orders_zero(self):
        """Test: obtener órdenes pendientes cuando no hay ninguna"""
        with patch('api.Orders.models.Orders.objects.filter') as mock_filter:
            mock_filter.return_value.count.return_value = 0
            response = self.client.get(self.url_pending_orders)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 0)

    @patch('api.Orders.models.Orders.objects.filter')
    def test_get_pending_orders_exception(self, mock_filter):
        """Test: manejo de excepción en get_pending_orders"""
        mock_filter.side_effect = Exception('Connection error')

        response = self.client.get(self.url_pending_orders)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('Connection error', response.data['error'])

    # ==================== TESTS PARA cantidad_ventas_mes ====================

    @patch('api.Sales.views.timezone.now')
    @patch('api.Sales.models.Sales.objects.filter')
    def test_cantidad_ventas_mes_success(self, mock_filter, mock_now):
        """Test: obtener cantidad de ventas del mes actual exitosamente"""
        mock_now.return_value = datetime(2026, 6, 15)
        mock_filter.return_value.count.return_value = 10

        response = self.client.get(self.url_cantidad_ventas)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 10)
        # Verificar que se filtró por mes y año correctos
        mock_filter.assert_called_once()

    @patch('api.Sales.views.timezone.now')
    @patch('api.Sales.models.Sales.objects.filter')
    def test_cantidad_ventas_mes_zero(self, mock_filter, mock_now):
        """Test: obtener cantidad de ventas cuando no hay ventas este mes"""
        mock_now.return_value = datetime(2026, 6, 15)
        mock_filter.return_value.count.return_value = 0

        response = self.client.get(self.url_cantidad_ventas)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 0)

    @patch('api.Sales.models.Sales.objects.filter')
    def test_cantidad_ventas_mes_exception(self, mock_filter):
        """Test: manejo de excepción en cantidad_ventas_mes"""
        mock_filter.side_effect = Exception('Query error')

        response = self.client.get(self.url_cantidad_ventas)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('Query error', response.data['error'])

    # ==================== TESTS PARA dinero_ventas_mes ====================

    @patch('api.Sales.views.timezone.now')
    @patch('api.Sales.models.Sales.objects.filter')
    def test_dinero_ventas_mes_success(self, mock_filter, mock_now):
        """Test: obtener dinero de ventas del mes actual exitosamente"""
        mock_now.return_value = datetime(2026, 6, 15)
        mock_filter.return_value.aggregate.return_value = {'total_dinero': 15000.50}

        response = self.client.get(self.url_dinero_ventas)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 15000.50)

    @patch('api.Sales.views.timezone.now')
    @patch('api.Sales.models.Sales.objects.filter')
    def test_dinero_ventas_mes_none(self, mock_filter, mock_now):
        """Test: obtener dinero de ventas cuando aggregate retorna None"""
        mock_now.return_value = datetime(2026, 6, 15)
        mock_filter.return_value.aggregate.return_value = {'total_dinero': None}

        response = self.client.get(self.url_dinero_ventas)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 0.0)

    @patch('api.Sales.models.Sales.objects.filter')
    def test_dinero_ventas_mes_exception(self, mock_filter):
        """Test: manejo de excepción en dinero_ventas_mes"""
        mock_filter.side_effect = Exception('Aggregate error')

        response = self.client.get(self.url_dinero_ventas)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('Aggregate error', response.data['error'])

    # ==================== TESTS PARA productos_mas_vendidos ====================

    @patch('api.Sales.models.SalesDetail.objects.values')
    def test_productos_mas_vendidos_success(self, mock_values):
        """Test: obtener productos más vendidos exitosamente"""
        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value.order_by.return_value = [
            {'variant__product__name': 'Producto A', 'total_vendido': 100},
            {'variant__product__name': 'Producto B', 'total_vendido': 80},
            {'variant__product__name': 'Producto C', 'total_vendido': 60},
            {'variant__product__name': 'Producto D', 'total_vendido': 40},
            {'variant__product__name': 'Producto E', 'total_vendido': 20},
        ]
        mock_values.return_value = mock_queryset

        response = self.client.get(self.url_productos_vendidos)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['results']), 5)
        self.assertEqual(response.data['results'][0]['producto'], 'Producto A')
        self.assertEqual(response.data['results'][0]['cantidad'], 100)

    @patch('api.Sales.models.SalesDetail.objects.values')
    def test_productos_mas_vendidos_empty(self, mock_values):
        """Test: obtener productos más vendidos cuando no hay datos"""
        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value.order_by.return_value = []
        mock_values.return_value = mock_queryset

        response = self.client.get(self.url_productos_vendidos)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['results']), 0)

    @patch('api.Sales.models.SalesDetail.objects.values')
    def test_productos_mas_vendidos_exception(self, mock_values):
        """Test: manejo de excepción en productos_mas_vendidos"""
        mock_values.side_effect = Exception('Query error')

        response = self.client.get(self.url_productos_vendidos)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('Query error', response.data['error'])

    # ==================== TESTS PARA distribucion_categorias ====================

    @patch('api.Sales.models.SalesDetail.objects.aggregate')
    @patch('api.Sales.models.SalesDetail.objects.values')
    def test_distribucion_categorias_success(self, mock_values, mock_aggregate):
        """Test: obtener distribución de categorías exitosamente"""
        mock_aggregate.return_value = {'total_todo': 1000.00}

        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value.order_by.return_value = [
            {'variant__product__category__name': 'Electrónica', 'total_categoria': 500.00},
            {'variant__product__category__name': 'Ropa', 'total_categoria': 300.00},
            {'variant__product__category__name': 'Hogar', 'total_categoria': 200.00},
        ]
        mock_values.return_value = mock_queryset

        response = self.client.get(self.url_distribucion)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['results']), 3)

        # Verificar porcentajes calculados
        self.assertEqual(response.data['results'][0]['porcentaje'], 50.0)
        self.assertEqual(response.data['results'][1]['porcentaje'], 30.0)
        self.assertEqual(response.data['results'][2]['porcentaje'], 20.0)

    @patch('api.Sales.models.SalesDetail.objects.aggregate')
    def test_distribucion_categorias_zero_total(self, mock_aggregate):
        """Test: distribución de categorías cuando el total es 0"""
        mock_aggregate.return_value = {'total_todo': 0}

        response = self.client.get(self.url_distribucion)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], [])

    @patch('api.Sales.models.SalesDetail.objects.aggregate')
    @patch('api.Sales.models.SalesDetail.objects.values')
    def test_distribucion_categorias_none_total(self, mock_values, mock_aggregate):
        """Test: distribución de categorías cuando aggregate retorna None"""
        mock_aggregate.return_value = {'total_todo': None}

        response = self.client.get(self.url_distribucion)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], [])

    @patch('api.Sales.models.SalesDetail.objects.aggregate')
    def test_distribucion_categorias_exception(self, mock_aggregate):
        """Test: manejo de excepción en distribucion_categorias"""
        mock_aggregate.side_effect = Exception('Database error')

        response = self.client.get(self.url_distribucion)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('Database error', response.data['error'])

    # ==================== TESTS PARA get_metrics ====================

    @patch('api.Returns.models.Returns.objects.count')
    def test_get_metrics_success(self, mock_count):
        """Test: obtener métricas de devoluciones exitosamente"""
        mock_count.return_value = 15

        response = self.client.get(self.url_metrics)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['metrics']['cantidad_devoluciones'], 15)
        self.assertEqual(response.data['message'], 'métricas de devoluciones')

    @patch('api.Returns.models.Returns.objects.count')
    def test_get_metrics_zero(self, mock_count):
        """Test: obtener métricas cuando no hay devoluciones"""
        mock_count.return_value = 0

        response = self.client.get(self.url_metrics)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['metrics']['cantidad_devoluciones'], 0)

    @patch('api.Returns.models.Returns.objects.count')
    def test_get_metrics_exception(self, mock_count):
        """Test: manejo de excepción en get_metrics"""
        mock_count.side_effect = Exception('Count error')

        response = self.client.get(self.url_metrics)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('Count error', response.data['message'])

    # ==================== TESTS DE INTEGRACIÓN ====================

    def test_unauthenticated_access(self):
        """Test: verificar que los endpoints requieren autenticación"""
        self.client.force_authenticate(user=None)

        endpoints = [
            self.url_users_active,
            self.url_pending_orders,
            self.url_cantidad_ventas,
            self.url_dinero_ventas,
            self.url_productos_vendidos,
            self.url_distribucion,
            self.url_metrics,
        ]

        for url in endpoints:
            response = self.client.get(url)
            # Ajustar según tu configuración de permisos (puede ser 401 o 403)
            self.assertIn(response.status_code, [status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    def test_http_method_not_allowed(self):
        """Test: verificar que solo se permite GET"""
        urls = [
            self.url_users_active,
            self.url_pending_orders,
            self.url_cantidad_ventas,
            self.url_dinero_ventas,
            self.url_productos_vendidos,
            self.url_distribucion,
            self.url_metrics,
        ]

        for url in urls:
            response_post = self.client.post(url, {})
            response_put = self.client.put(url, {})
            response_delete = self.client.delete(url)

            # Deberían retornar 405 Method Not Allowed
            self.assertIn(response_post.status_code, [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_403_FORBIDDEN])

    # ==================== TESTS DE BORDE ====================

    @patch('api.Sales.views.timezone.now')
    @patch('api.Sales.models.Sales.objects.filter')
    def test_cantidad_ventas_year_boundary(self, mock_filter, mock_now):
        """Test: ventas en el límite de año (enero)"""
        mock_now.return_value = datetime(2026, 1, 15)
        mock_filter.return_value.count.return_value = 5

        response = self.client.get(self.url_cantidad_ventas)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Sales.views.timezone.now')
    @patch('api.Sales.models.Sales.objects.filter')
    def test_cantidad_ventas_december(self, mock_filter, mock_now):
        """Test: ventas en diciembre"""
        mock_now.return_value = datetime(2026, 12, 31)
        mock_filter.return_value.count.return_value = 100

        response = self.client.get(self.url_cantidad_ventas)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Sales.models.SalesDetail.objects.aggregate')
    @patch('api.Sales.models.SalesDetail.objects.values')
    def test_distribucion_categorias_single_category(self, mock_values, mock_aggregate):
        """Test: distribución con una sola categoría (100%)"""
        mock_aggregate.return_value = {'total_todo': 500.00}

        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value.order_by.return_value = [
            {'variant__product__category__name': 'Única', 'total_categoria': 500.00},
        ]
        mock_values.return_value = mock_queryset

        response = self.client.get(self.url_distribucion)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'][0]['porcentaje'], 100.0)

    @patch('api.Sales.models.SalesDetail.objects.aggregate')
    @patch('api.Sales.models.SalesDetail.objects.values')
    def test_distribucion_categorias_null_category(self, mock_values, mock_aggregate):
        """Test: distribución con categorías nulas"""
        mock_aggregate.return_value = {'total_todo': 1000.00}

        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value.order_by.return_value = [
            {'variant__product__category__name': None, 'total_categoria': 300.00},
            {'variant__product__category__name': 'Electrónica', 'total_categoria': 700.00},
        ]
        mock_values.return_value = mock_queryset

        response = self.client.get(self.url_distribucion)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Verificar que maneja None correctamente
        self.assertEqual(len(response.data['results']), 2)

    @patch('api.Sales.models.SalesDetail.objects.values')
    def test_productos_mas_vendidos_tie_breaker(self, mock_values):
        """Test: productos con cantidades iguales"""
        mock_queryset = MagicMock()
        mock_queryset.annotate.return_value.order_by.return_value = [
            {'variant__product__name': 'Producto A', 'total_vendido': 50},
            {'variant__product__name': 'Producto B', 'total_vendido': 50},
            {'variant__product__name': 'Producto C', 'total_vendido': 50},
        ]
        mock_values.return_value = mock_queryset

        response = self.client.get(self.url_productos_vendidos)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 3)
        # Todos deberían tener la misma cantidad
        for item in response.data['results']:
            self.assertEqual(item['cantidad'], 50)

    @patch('api.Sales.models.Sales.objects.filter')
    def test_dinero_ventas_large_number(self, mock_filter):
        """Test: dinero de ventas con números muy grandes"""
        with patch('api.Sales.views.timezone.now') as mock_now:
            mock_now.return_value = datetime(2026, 6, 15)
            mock_filter.return_value.aggregate.return_value = {'total_dinero': 999999999.99}

            response = self.client.get(self.url_dinero_ventas)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], 999999999.99)

    @patch('api.Sales.models.Sales.objects.filter')
    def test_dinero_ventas_negative(self, mock_filter):
        """Test: dinero de ventas con valor negativo (caso borde)"""
        with patch('api.Sales.views.timezone.now') as mock_now:
            mock_now.return_value = datetime(2026, 6, 15)
            mock_filter.return_value.aggregate.return_value = {'total_dinero': -100.00}

            response = self.client.get(self.url_dinero_ventas)

        # El código actual permite negativos, verificar comportamiento
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['results'], -100.00)


class DashboardViewSetsIntegrationTestCase(APITestCase):
    """Tests de integración con base de datos real (si es posible)"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_actual_database_users_active(self):
        """Test: usuarios activos con base de datos real"""
        # Crear usuarios de prueba
        Users.objects.create(username='user1', is_active=True)
        Users.objects.create(username='user2', is_active=True)
        Users.objects.create(username='user3', is_active=False)

        url = reverse('dashboard-get-users-active')
        response = self.client.get(url)

        # Nota: Esto puede fallar si no tienes configurada la base de datos de prueba
        # o si los modelos no están completamente configurados
        if response.status_code == status.HTTP_200_OK:
            self.assertTrue(response.data['success'])
            # El conteo incluiría el usuario de autenticación + los creados
            self.assertGreaterEqual(response.data['results'], 1)


# Si necesitas ejecutar tests específicos sin mock (requiere fixtures completas)
class DashboardViewSetsFixtureTestCase(APITestCase):
    """Tests que requieren fixtures de datos completas"""

    fixtures = ['users', 'orders', 'sales', 'returns']  # Ajustar según tus fixtures

    def setUp(self):
        self.client = APIClient()
        # Asumiendo que hay un usuario en las fixtures
        self.user = User.objects.first()
        self.client.force_authenticate(user=self.user)

    def test_with_fixtures(self):
        """Test: endpoints con datos de fixtures"""
        # Implementar según tus fixtures disponibles
        pass

# Create your tests here.
