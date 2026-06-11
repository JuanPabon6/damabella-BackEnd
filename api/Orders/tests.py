from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status, filters, permissions
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock, ANY
from django.core.exceptions import MultipleObjectsReturned
from django.db.utils import IntegrityError
from rest_framework.response import Response

from api.Orders.models import Orders, OrdersDetail, PaymentMethods
from api.Orders.serializers import OrdersSerializers, OrderDetailSerializer, PaymentMethodsSerializer
from api.Orders.views import OrdersViewSet, OrdersDetailsViewSet, PaymentMethodsViewSet
from api.States.models import States
from .services import Export_orders_list


User = get_user_model()


# =============================================================================
# TESTS PARA OrdersViewSet
# =============================================================================

class OrdersViewSetTestCase(APITestCase):
    """Test cases para OrdersViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_orders = reverse('orders-get-orders')
        self.url_create_orders = reverse('orders-create-orders')
        self.url_search_orders = reverse('orders-search-orders')
        self.url_export_orders = reverse('orders-export-orders')
        self.url_get_my_orders = reverse('orders-get-my-orders')

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = OrdersViewSet()
        self.assertEqual(viewset.queryset.model, Orders)
        self.assertEqual(viewset.serializer_class, OrdersSerializers)
        self.assertEqual(viewset.required_module, 'Pedidos')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        self.assertIn(permissions.AllowAny, viewset.permission_classes)
        expected_fields = [
            'id_order', 'number_order', 'client', 'order_date', 'payment_method',
            'address_shipment', 'person_receives', 'subtotal', 'iva', 'total',
            'observations', 'state',
        ]
        self.assertEqual(viewset.search_fields, expected_fields)

    # ==================== TESTS PARA get_orders ====================

    @patch('api.Orders.views.OrdersViewSet.get_queryset')
    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_get_orders_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de pedidos exitosamente"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_get_queryset.return_value = mock_queryset
        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'number_order': 'ORD-001', 'total': 100.00},
            {'id': 2, 'number_order': 'ORD-002', 'total': 200.00},
        ]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_orders)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'pedidos obtenidos')
        self.assertEqual(len(response.data['results']), 2)

    @patch('api.Orders.views.OrdersViewSet.get_queryset')
    def test_get_orders_empty(self, mock_get_queryset):
        """Test: obtener lista de pedidos vacia (404)"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_get_queryset.return_value = mock_queryset
        response = self.client.get(self.url_get_orders)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no se encontraron', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_queryset')
    def test_get_orders_exception(self, mock_get_queryset):
        """Test: excepcion en get_orders"""
        mock_get_queryset.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_orders)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('database error', response.data['message'].lower())

    # ==================== TESTS PARA get_orders_by_id ====================

    @patch('api.Orders.views.OrdersViewSet.get_object')
    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_get_orders_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener pedido por ID exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'number_order': 'ORD-001', 'total': 100.00}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('orders-get-orders-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'pedido obtenido')
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_get_orders_by_id_not_found(self, mock_get_object):
        """Test: pedido no encontrado"""
        mock_get_object.side_effect = Orders.DoesNotExist("No existe")
        url = reverse('orders-get-orders-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_get_orders_by_id_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('orders-get-orders-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_get_orders_by_id_exception(self, mock_get_object):
        """Test: excepcion generica"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('orders-get-orders-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA create_orders ====================

    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_create_orders_success(self, mock_get_serializer):
        """Test: crear pedido exitosamente (201 Created)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'number_order': 'ORD-001', 'total': 100.00}
        mock_get_serializer.return_value = mock_serializer
        data = {'number_order': 'ORD-001', 'client': 1, 'total': 100.00}
        response = self.client.post(self.url_create_orders, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'creado exitosamente')
        self.assertIn('object', response.data)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_create_orders_validation_error(self, mock_get_serializer):
        """Test: crear pedido con datos invalidos (ValidationError)"""
        from rest_framework.exceptions import ValidationError
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'number_order': ['Requerido']})
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_orders, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('validation', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_create_orders_multiple_objects(self, mock_get_serializer):
        """Test: manejo de MultipleObjectsReturned en create_orders"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = MultipleObjectsReturned("Multiples objetos")
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_orders, {'number_order': 'ORD-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_create_orders_exception(self, mock_get_serializer):
        """Test: excepcion generica en create_orders"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Unexpected error')
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_orders, {'number_order': 'ORD-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_create_orders_integrity_error(self, mock_get_serializer):
        """Test: crear pedido con IntegrityError"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_orders, {'number_order': 'ORD-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA delete_orders ====================

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_delete_orders_success(self, mock_get_object):
        """Test: eliminar pedido exitosamente"""
        mock_order = MagicMock()
        mock_order.delete = MagicMock()
        mock_get_object.return_value = mock_order
        url = reverse('orders-delete-orders', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('eliminado', response.data['message'].lower())
        mock_order.delete.assert_called_once()

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_delete_orders_not_found(self, mock_get_object):
        """Test: eliminar pedido inexistente"""
        mock_get_object.side_effect = Orders.DoesNotExist("No existe")
        url = reverse('orders-delete-orders', kwargs={'pk': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_delete_orders_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('orders-delete-orders', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_delete_orders_exception(self, mock_get_object):
        """Test: excepcion generica en delete_orders"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('orders-delete-orders', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_delete_orders_integrity_error(self, mock_get_object):
        """Test: eliminar pedido con IntegrityError"""
        mock_order = MagicMock()
        mock_order.delete.side_effect = IntegrityError("Foreign key constraint")
        mock_get_object.return_value = mock_order
        url = reverse('orders-delete-orders', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA update_orders ====================

    @patch('api.Orders.views.OrdersViewSet.get_object')
    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_update_orders_success(self, mock_get_serializer, mock_get_object):
        """Test: actualizar pedido exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'number_order': 'ORD-001-UPD', 'total': 150.00}
        mock_get_serializer.return_value = mock_serializer
        data = {'number_order': 'ORD-001-UPD', 'total': 150.00}
        url = reverse('orders-update-orders', kwargs={'pk': 1})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'pedido actualizado exitosamente')
        self.assertIn('object', response.data)

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_update_orders_not_found(self, mock_get_object):
        """Test: actualizar pedido inexistente"""
        mock_get_object.side_effect = Orders.DoesNotExist("No existe")
        url = reverse('orders-update-orders', kwargs={'pk': 999})
        response = self.client.put(url, {'number_order': 'ORD-999'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_update_orders_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('orders-update-orders', kwargs={'pk': 1})
        response = self.client.put(url, {'number_order': 'ORD-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_object')
    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_update_orders_exception(self, mock_get_serializer, mock_get_object):
        """Test: excepcion generica en update_orders"""
        mock_get_object.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Validation error')
        mock_get_serializer.return_value = mock_serializer
        url = reverse('orders-update-orders', kwargs={'pk': 1})
        response = self.client.put(url, {'number_order': 'ORD-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Orders.views.OrdersViewSet.get_object')
    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_update_orders_integrity_error(self, mock_get_serializer, mock_get_object):
        """Test: actualizar pedido con IntegrityError"""
        mock_get_object.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer
        url = reverse('orders-update-orders', kwargs={'pk': 1})
        response = self.client.put(url, {'number_order': 'ORD-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA patch_state ====================

    @patch('api.Orders.views.OrdersViewSet.get_object')
    @patch('api.Orders.models.States.objects.get')
    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_patch_state_success(self, mock_get_serializer, mock_states_get, mock_get_object):
        """Test: actualizar estado de pedido exitosamente"""
        mock_order = MagicMock()
        mock_order.state = None
        mock_order.save = MagicMock()
        mock_get_object.return_value = mock_order

        mock_state = MagicMock()
        mock_state.id_state = 1
        mock_states_get.return_value = mock_state

        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'state': {'id_state': 1, 'name': 'Pendiente'}}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('orders-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'estado actualizado')
        self.assertIn('object', response.data)
        mock_states_get.assert_called_once_with(id_state=1)
        mock_order.save.assert_called_once()

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_patch_state_missing_state(self, mock_get_object):
        """Test: patch_state sin enviar estado"""
        mock_get_object.return_value = MagicMock()
        url = reverse('orders-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('no hay estado', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_object')
    @patch('api.Orders.models.States.objects.get')
    def test_patch_state_state_not_found(self, mock_states_get, mock_get_object):
        """Test: patch_state con estado inexistente"""
        mock_get_object.return_value = MagicMock()
        mock_states_get.side_effect = States.DoesNotExist("No existe")
        url = reverse('orders-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_patch_state_not_found(self, mock_get_object):
        """Test: patch_state en pedido inexistente"""
        mock_get_object.side_effect = Orders.DoesNotExist("No existe")
        url = reverse('orders-patch-state', kwargs={'pk': 999})
        response = self.client.patch(url, {'state': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_patch_state_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en patch_state"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('orders-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Orders.views.OrdersViewSet.get_object')
    def test_patch_state_exception(self, mock_get_object):
        """Test: excepcion generica en patch_state"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('orders-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 1}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA search_orders ====================

    @patch('api.Orders.views.OrdersViewSet.get_queryset')
    @patch('api.Orders.views.OrdersViewSet.filter_queryset')
    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    def test_search_orders_success(self, mock_get_serializer, mock_filter_queryset, mock_get_queryset):
        """Test: buscar pedidos con resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'number_order': 'ORD-001'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_search_orders, {'search': 'ORD-001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'resultados obtenidos')

    @patch('api.Orders.views.OrdersViewSet.get_queryset')
    def test_search_orders_exception(self, mock_get_queryset):
        """Test: excepcion en search_orders"""
        mock_get_queryset.side_effect = Exception('Search error')
        response = self.client.get(self.url_search_orders)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA export_orders ====================

    @patch('api.Orders.models.Orders.objects.select_related')
    def test_export_orders_success(self, mock_select_related):
        mock_queryset = MagicMock()
        mock_queryset.prefetch_related.return_value = mock_queryset
        mock_select_related.return_value = mock_queryset
        with patch('api.Orders.views.Export_orders_list') as mock_export:
            mock_export.return_value = Response({'message': 'Exportado'}, status=status.HTTP_200_OK)
            response = self.client.get(self.url_export_orders)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_select_related.assert_called_once_with('client', 'payment_method', 'state')

    @patch('api.Orders.models.Orders.objects.select_related')
    def test_export_orders_exception(self, mock_select_related):
        mock_select_related.side_effect = Exception('Export error')
        response = self.client.get(self.url_export_orders)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA get_my_orders ====================

    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    @patch('api.Orders.models.Orders.objects.filter')
    @patch('api.Users.models.Clients.objects.get')
    def test_get_my_orders_success(self, mock_clients_get, mock_orders_filter, mock_get_serializer):
        """Test: obtener mis pedidos exitosamente"""
        mock_client = MagicMock()
        mock_client.id = 1
        mock_clients_get.return_value = mock_client

        mock_orders = MagicMock()
        mock_orders.exists.return_value = True
        mock_orders.order_by.return_value = mock_orders
        mock_orders_filter.return_value = mock_orders

        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'number_order': 'ORD-001'}]
        mock_get_serializer.return_value = mock_serializer

        response = self.client.get(self.url_get_my_orders)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'Tus pedidos fueron obtenidos con exito')
        self.assertEqual(len(response.data['results']), 1)
        mock_clients_get.assert_called_once_with(email__iexact=self.user.email)
        mock_orders_filter.assert_called_once_with(client=mock_client)

    @patch('api.Orders.views.OrdersViewSet.get_serializer')
    @patch('api.Orders.models.Orders.objects.filter')
    @patch('api.Users.models.Clients.objects.get')
    def test_get_my_orders_create_client(self, mock_clients_get, mock_orders_filter, mock_get_serializer):
        """Test: crear cliente si no existe y obtener pedidos"""
        mock_clients_get.side_effect = [
            Exception("No existe"),  # Primera llamada falla
            MagicMock(id=1)  # Segunda llamada (create) retorna el cliente
        ]

        with patch('api.Users.models.Clients.objects.create') as mock_create:
            mock_client = MagicMock()
            mock_client.id = 1
            mock_create.return_value = mock_client

            mock_orders = MagicMock()
            mock_orders.exists.return_value = False
            mock_orders.order_by.return_value = mock_orders
            mock_orders_filter.return_value = mock_orders

            response = self.client.get(self.url_get_my_orders)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertEqual(response.data['results'], [])
            self.assertIn('no tienes pedidos', response.data['message'].lower())
            mock_create.assert_called_once()

    @patch('api.Users.models.Clients.objects.get')
    def test_get_my_orders_exception(self, mock_clients_get):
        """Test: excepcion en get_my_orders"""
        mock_clients_get.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_my_orders)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('error', response.data['message'].lower())

    def test_get_my_orders_requires_authentication(self):
        """Test: get_my_orders requiere autenticacion"""
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url_get_my_orders)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==================== TESTS DE METODOS HTTP ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar metodos HTTP no soportados"""
        response_post = self.client.post(self.url_get_orders, {})
        response_put = self.client.put(self.url_get_orders, {})
        response_delete = self.client.delete(self.url_get_orders)
        self.assertIn(response_post.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])

    # ==================== TESTS DE AUTENTICACION ====================

    def test_allow_any_permission(self):
        """Test: verificar que AllowAny funciona"""
        self.client.force_authenticate(user=None)
        with patch('api.Orders.views.OrdersViewSet.get_queryset') as mock_qs, \
             patch('api.Orders.views.OrdersViewSet.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_s = MagicMock()
            mock_s.data = []
            mock_ser.return_value = mock_s
            response = self.client.get(self.url_get_orders)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =============================================================================
# TESTS PARA OrdersDetailsViewSet
# =============================================================================

class OrdersDetailsViewSetTestCase(APITestCase):
    """Test cases para OrdersDetailsViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_details = reverse('orders-details-get-details')
        self.url_search_details = reverse('orders-details-search-details')

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = OrdersDetailsViewSet()
        self.assertEqual(viewset.queryset.model, OrdersDetail)
        self.assertEqual(viewset.serializer_class, OrderDetailSerializer)
        self.assertEqual(viewset.required_module, 'Pedidos')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        expected_fields = ['id_detail', 'order', 'variant', 'quantity', 'sales_price', 'subtotal']
        self.assertEqual(viewset.search_fields, expected_fields)

    # ==================== TESTS PARA get_details ====================

    @patch('api.Orders.views.OrdersDetailsViewSet.get_queryset')
    @patch('api.Orders.views.OrdersDetailsViewSet.get_serializer')
    def test_get_details_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de detalles exitosamente"""
        mock_get_queryset.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'order': 1, 'variant': 1, 'quantity': 10}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_details)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalles obtenidos')
        self.assertEqual(len(response.data['results']), 1)

    @patch('api.Orders.views.OrdersDetailsViewSet.get_queryset')
    def test_get_details_value_error(self, mock_get_queryset):
        """Test: ValueError en get_details"""
        mock_get_queryset.side_effect = ValueError("Invalid value")
        response = self.client.get(self.url_get_details)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error de valores', response.data['message'].lower())

    @patch('api.Orders.views.OrdersDetailsViewSet.get_queryset')
    def test_get_details_exception(self, mock_get_queryset):
        """Test: excepcion generica en get_details"""
        mock_get_queryset.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_details)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA get_details_by_id ====================

    @patch('api.Orders.views.OrdersDetailsViewSet.get_object')
    @patch('api.Orders.views.OrdersDetailsViewSet.get_serializer')
    def test_get_details_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener detalle por ID exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'order': 1, 'variant': 1, 'quantity': 10}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('orders-details-get-details-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalle obtenido')
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.Orders.views.OrdersDetailsViewSet.get_object')
    def test_get_details_by_id_not_found(self, mock_get_object):
        """Test: detalle no encontrado"""
        mock_get_object.side_effect = OrdersDetail.DoesNotExist("No existe")
        url = reverse('orders-details-get-details-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Orders.views.OrdersDetailsViewSet.get_object')
    def test_get_details_by_id_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('orders-details-get-details-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Orders.views.OrdersDetailsViewSet.get_object')
    def test_get_details_by_id_exception(self, mock_get_object):
        """Test: excepcion generica"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('orders-details-get-details-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA get_details_by_order ====================

    @patch('api.Orders.models.OrdersDetail.objects.filter')
    @patch('api.Orders.views.OrdersDetailsViewSet.get_serializer')
    def test_get_details_by_order_success(self, mock_get_serializer, mock_filter):
        """Test: obtener detalles por pedido exitosamente"""
        mock_details = MagicMock()
        mock_details.exists.return_value = True
        mock_filter.return_value = mock_details
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'order': 1, 'quantity': 10}]
        mock_get_serializer.return_value = mock_serializer
        url = reverse('orders-details-get-details-by-order', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalles obtenidos')
        mock_filter.assert_called_once_with(order=1)

    @patch('api.Orders.models.OrdersDetail.objects.filter')
    def test_get_details_by_order_empty(self, mock_filter):
        """Test: pedido sin detalles (404)"""
        mock_details = MagicMock()
        mock_details.exists.return_value = False
        mock_filter.return_value = mock_details
        url = reverse('orders-details-get-details-by-order', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no se encontraron', response.data['message'].lower())

    @patch('api.Orders.models.OrdersDetail.objects.filter')
    def test_get_details_by_order_value_error(self, mock_filter):
        """Test: ValueError en get_details_by_order"""
        mock_filter.side_effect = ValueError("Invalid value")
        url = reverse('orders-details-get-details-by-order', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error de valores', response.data['message'].lower())

    @patch('api.Orders.models.OrdersDetail.objects.filter')
    def test_get_details_by_order_exception(self, mock_filter):
        """Test: excepcion generica"""
        mock_filter.side_effect = Exception('Database error')
        url = reverse('orders-details-get-details-by-order', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA search_details ====================

    @patch('api.Orders.views.OrdersDetailsViewSet.get_queryset')
    @patch('api.Orders.views.OrdersDetailsViewSet.filter_queryset')
    @patch('api.Orders.views.OrdersDetailsViewSet.get_serializer')
    def test_search_details_success(self, mock_get_serializer, mock_filter_queryset, mock_get_queryset):
        """Test: buscar detalles con resultados"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_get_queryset.return_value = mock_queryset
        mock_filtered = MagicMock()
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'quantity': 10}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_search_details, {'search': '10'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalles encontrados')

    @patch('api.Orders.views.OrdersDetailsViewSet.get_queryset')
    def test_search_details_empty(self, mock_get_queryset):
        """Test: buscar detalles sin resultados (400)"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_get_queryset.return_value = mock_queryset
        response = self.client.get(self.url_search_details)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('no hay detalles', response.data['message'].lower())

    @patch('api.Orders.views.OrdersDetailsViewSet.get_queryset')
    def test_search_details_exception(self, mock_get_queryset):
        """Test: excepcion en search_details"""
        mock_get_queryset.side_effect = Exception('Search error')
        response = self.client.get(self.url_search_details)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS DE METODOS HTTP ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar metodos HTTP no soportados"""
        response_post = self.client.post(self.url_get_details, {})
        response_put = self.client.put(self.url_get_details, {})
        response_delete = self.client.delete(self.url_get_details)
        self.assertIn(response_post.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])


# =============================================================================
# TESTS PARA PaymentMethodsViewSet
# =============================================================================

class PaymentMethodsViewSetTestCase(APITestCase):
    """Test cases para PaymentMethodsViewSet (ModelViewSet)"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = PaymentMethodsViewSet()
        self.assertEqual(viewset.queryset.model, PaymentMethods)
        self.assertEqual(viewset.serializer_class, PaymentMethodsSerializer)
        self.assertEqual(viewset.required_module, 'Orders')
        self.assertIn(permissions.AllowAny, viewset.permission_classes)

    def test_list_payment_methods(self):
        """Test: listar metodos de pago (ModelViewSet list)"""
        with patch('api.Orders.views.PaymentMethodsViewSet.get_queryset') as mock_qs, \
             patch('api.Orders.views.PaymentMethodsViewSet.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_serializer = MagicMock()
            mock_serializer.data = [{'id': 1, 'name': 'Efectivo'}]
            mock_ser.return_value = mock_serializer
            response = self.client.get(reverse('payment-methods-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_payment_method(self):
        """Test: obtener metodo de pago por ID (ModelViewSet retrieve)"""
        with patch('api.Orders.views.PaymentMethodsViewSet.get_object') as mock_obj, \
             patch('api.Orders.views.PaymentMethodsViewSet.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock(id=1)
            mock_serializer = MagicMock()
            mock_serializer.data = {'id': 1, 'name': 'Efectivo'}
            mock_ser.return_value = mock_serializer
            response = self.client.get(reverse('payment-methods-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_payment_method(self):
        """Test: crear metodo de pago (ModelViewSet create)"""
        with patch('api.Orders.views.PaymentMethodsViewSet.get_serializer') as mock_ser:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1, 'name': 'Tarjeta'}
            mock_ser.return_value = mock_serializer
            response = self.client.post(reverse('payment-methods-list'), {'name': 'Tarjeta'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_payment_method(self):
        """Test: actualizar metodo de pago (ModelViewSet update)"""
        with patch('api.Orders.views.PaymentMethodsViewSet.get_object') as mock_obj, \
             patch('api.Orders.views.PaymentMethodsViewSet.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock(id=1)
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1, 'name': 'Transferencia'}
            mock_ser.return_value = mock_serializer
            response = self.client.put(reverse('payment-methods-detail', kwargs={'pk': 1}), {'name': 'Transferencia'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_payment_method(self):
        """Test: eliminar metodo de pago (ModelViewSet destroy)"""
        with patch('api.Orders.views.PaymentMethodsViewSet.get_object') as mock_obj:
            mock_payment = MagicMock()
            mock_payment.delete = MagicMock()
            mock_obj.return_value = mock_payment
            response = self.client.delete(reverse('payment-methods-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_allow_any_permission(self):
        """Test: verificar que AllowAny funciona"""
        self.client.force_authenticate(user=None)
        with patch('api.Orders.views.PaymentMethodsViewSet.get_queryset') as mock_qs, \
             patch('api.Orders.views.PaymentMethodsViewSet.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_s = MagicMock()
            mock_s.data = []
            mock_ser.return_value = mock_s
            response = self.client.get(reverse('payment-methods-list'))
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

# Create your tests here.
