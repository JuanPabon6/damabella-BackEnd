from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status, filters
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock, ANY
from django.core.exceptions import MultipleObjectsReturned
from django.db.utils import IntegrityError
from django.db import transaction
from rest_framework.response import Response

from api.Sales.models import Sales, SalesDetail
from api.Sales.serializers import SalesSerializer, SalesDetailsSerializer
from api.Sales.views import SalesViewSets, SalesDetailViewsets
from api.Inventory.services import add_stock
from .services import Export_sales_list


User = get_user_model()


# =============================================================================
# TESTS PARA SalesViewSets
# =============================================================================

class SalesViewSetsTestCase(APITestCase):
    """Test cases para SalesViewSets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_sales = reverse('sales-get-sales')
        self.url_create_sale = reverse('sales-create-sale')
        self.url_search_sales = reverse('sales-search-sales')
        self.url_export_sales = reverse('sales-export-sales')

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = SalesViewSets()
        self.assertEqual(viewset.queryset.model, Sales)
        self.assertEqual(viewset.serializer_class, SalesSerializer)
        self.assertEqual(viewset.required_module, 'Ventas')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        expected_fields = [
            'id_sale', 'number_sale', 'client', 'date_sale', 'state', 'payment_method',
            'subtotal', 'iva', 'total', 'output_executing', 'return_executing',
            'void', 'void_reason'
        ]
        self.assertEqual(viewset.search_fields, expected_fields)

    # ==================== TESTS PARA get_sales ====================

    @patch('api.Sales.views.SalesViewSets.get_queryset')
    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_get_sales_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de ventas exitosamente"""
        mock_queryset = MagicMock()
        mock_queryset.__bool__ = lambda self: True
        mock_get_queryset.return_value = mock_queryset
        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'number_sale': 'VEN-001', 'total': 100.00},
            {'id': 2, 'number_sale': 'VEN-002', 'total': 200.00},
        ]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_sales)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'ventas obtenidas')
        self.assertEqual(len(response.data['results']), 2)

    @patch('api.Sales.views.SalesViewSets.get_queryset')
    def test_get_sales_empty(self, mock_get_queryset):
        """Test: obtener lista de ventas vacia (404)"""
        mock_queryset = MagicMock()
        mock_queryset.__bool__ = lambda self: False
        mock_get_queryset.return_value = mock_queryset
        response = self.client.get(self.url_get_sales)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existen', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_queryset')
    def test_get_sales_exception(self, mock_get_queryset):
        """Test: excepcion en get_sales"""
        mock_get_queryset.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_sales)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('database error', response.data['message'].lower())

    # ==================== TESTS PARA get_sales_by_id ====================

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_get_sales_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener venta por ID exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'number_sale': 'VEN-001', 'total': 100.00}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('sales-get-sales-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'venta obtenida')
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_get_sales_by_id_not_found(self, mock_get_object):
        """Test: venta no encontrada"""
        mock_get_object.side_effect = Sales.DoesNotExist("No existe")
        url = reverse('sales-get-sales-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_get_sales_by_id_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('sales-get-sales-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_get_sales_by_id_exception(self, mock_get_object):
        """Test: excepcion generica"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('sales-get-sales-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA create_sale ====================

    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_create_sale_success(self, mock_get_serializer):
        """Test: crear venta exitosamente (201 Created)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'number_sale': 'VEN-001', 'total': 100.00}
        mock_get_serializer.return_value = mock_serializer
        data = {'number_sale': 'VEN-001', 'client': 1, 'total': 100.00}
        response = self.client.post(self.url_create_sale, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'venta creada exitosamente')
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_create_sale_validation_error(self, mock_get_serializer):
        """Test: crear venta con datos invalidos (ValidationError)"""
        from rest_framework.exceptions import ValidationError
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'number_sale': ['Requerido']})
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_sale, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_create_sale_integrity_error(self, mock_get_serializer):
        """Test: crear venta con IntegrityError"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer
        data = {'number_sale': 'VEN-001'}
        response = self.client.post(self.url_create_sale, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_create_sale_exception(self, mock_get_serializer):
        """Test: excepcion generica en create_sale"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Unexpected error')
        mock_get_serializer.return_value = mock_serializer
        data = {'number_sale': 'VEN-001'}
        response = self.client.post(self.url_create_sale, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA delete_sale ====================

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('api.Sales.views.add_stock')
    @patch('django.db.transaction.atomic')
    def test_delete_sale_success(self, mock_atomic, mock_add_stock, mock_get_object):
        """Test: eliminar venta anulada exitosamente"""
        mock_state = MagicMock()
        mock_state.name_state = 'Anulado'

        mock_detail1 = MagicMock()
        mock_detail1.variant = MagicMock(id=1)
        mock_detail1.quantity = 5
        mock_detail2 = MagicMock()
        mock_detail2.variant = MagicMock(id=2)
        mock_detail2.quantity = 3

        mock_sale = MagicMock()
        mock_sale.state = mock_state
        mock_sale.sales_details.all.return_value = [mock_detail1, mock_detail2]
        mock_sale.delete = MagicMock()
        mock_get_object.return_value = mock_sale

        url = reverse('sales-delete-sale', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'venta eliminada exitosamente')
        mock_sale.delete.assert_called_once()
        mock_add_stock.assert_any_call(mock_detail1.variant, 5)
        mock_add_stock.assert_any_call(mock_detail2.variant, 3)
        self.assertEqual(mock_add_stock.call_count, 2)

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_sale_not_voided(self, mock_atomic, mock_get_object):
        """Test: intentar eliminar venta no anulada"""
        mock_state = MagicMock()
        mock_state.name_state = 'Pendiente'

        mock_sale = MagicMock()
        mock_sale.state = mock_state
        mock_get_object.return_value = mock_sale

        url = reverse('sales-delete-sale', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('solo se pueden eliminar', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_sale_not_found(self, mock_atomic, mock_get_object):
        """Test: eliminar venta inexistente"""
        mock_get_object.side_effect = Sales.DoesNotExist("No existe")
        url = reverse('sales-delete-sale', kwargs={'pk': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_sale_multiple_objects(self, mock_atomic, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('sales-delete-sale', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_sale_exception(self, mock_atomic, mock_get_object):
        """Test: excepcion generica en delete_sale"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('sales-delete-sale', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('api.Sales.views.add_stock')
    @patch('django.db.transaction.atomic')
    def test_delete_sale_integrity_error(self, mock_atomic, mock_add_stock, mock_get_object):
        """Test: eliminar venta con IntegrityError"""
        mock_state = MagicMock()
        mock_state.name_state = 'Anulado'

        mock_sale = MagicMock()
        mock_sale.state = mock_state
        mock_sale.sales_details.all.return_value = []
        mock_sale.delete.side_effect = IntegrityError("Foreign key constraint")
        mock_get_object.return_value = mock_sale

        url = reverse('sales-delete-sale', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA update_sales ====================

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_update_sales_success(self, mock_get_serializer, mock_get_object):
        """Test: actualizar venta exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'number_sale': 'VEN-001-UPD', 'total': 150.00}
        mock_get_serializer.return_value = mock_serializer
        data = {'number_sale': 'VEN-001-UPD', 'total': 150.00}
        url = reverse('sales-update-sales', kwargs={'pk': 1})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'venta actualizada exitosamente')
        self.assertIn('object', response.data)

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_update_sales_not_found(self, mock_get_object):
        """Test: actualizar venta inexistente"""
        mock_get_object.side_effect = Sales.DoesNotExist("No existe")
        url = reverse('sales-update-sales', kwargs={'pk': 999})
        response = self.client.put(url, {'number_sale': 'VEN-999'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_update_sales_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('sales-update-sales', kwargs={'pk': 1})
        response = self.client.put(url, {'number_sale': 'VEN-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_update_sales_validation_error(self, mock_get_serializer, mock_get_object):
        """Test: actualizar venta con datos invalidos"""
        from rest_framework.exceptions import ValidationError
        mock_get_object.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'number_sale': ['Requerido']})
        mock_get_serializer.return_value = mock_serializer
        url = reverse('sales-update-sales', kwargs={'pk': 1})
        response = self.client.put(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_update_sales_integrity_error(self, mock_get_serializer, mock_get_object):
        """Test: actualizar venta con IntegrityError"""
        mock_get_object.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer
        url = reverse('sales-update-sales', kwargs={'pk': 1})
        response = self.client.put(url, {'number_sale': 'VEN-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_update_sales_exception(self, mock_get_serializer, mock_get_object):
        """Test: excepcion generica en update_sales"""
        mock_get_object.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Server error')
        mock_get_serializer.return_value = mock_serializer
        url = reverse('sales-update-sales', kwargs={'pk': 1})
        response = self.client.put(url, {'number_sale': 'VEN-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA search_sales ====================

    @patch('api.Sales.views.SalesViewSets.filter_queryset')
    @patch('api.Sales.views.SalesViewSets.get_queryset')
    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_search_sales_success(self, mock_get_serializer, mock_get_queryset, mock_filter_queryset):
        """Test: buscar ventas con resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'number_sale': 'VEN-001'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_search_sales, {'search': 'VEN-001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'ventas obtenidas')

    @patch('api.Sales.views.SalesViewSets.get_queryset')
    def test_search_sales_exception(self, mock_get_queryset):
        """Test: excepcion en search_sales"""
        mock_get_queryset.side_effect = Exception('Search error')
        response = self.client.get(self.url_search_sales)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA patch_state ====================

    @patch('api.Sales.views.SalesViewSets.get_object')
    @patch('api.Sales.views.SalesViewSets.get_serializer')
    def test_patch_state_success(self, mock_get_serializer, mock_get_object):
        """Test: actualizar estado de venta exitosamente"""
        mock_state = MagicMock()
        mock_state.name_state = 'Pendiente'

        mock_sale = MagicMock()
        mock_sale.state = mock_state
        mock_sale.state_id_state = 1
        mock_sale.save = MagicMock()
        mock_get_object.return_value = mock_sale

        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'state_id_state': 2, 'state': {'id_state': 2, 'name': 'Enviado'}}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('sales-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'estado actualizado exitosamente')
        self.assertIn('object', response.data)
        self.assertEqual(mock_sale.state_id_state, 2)
        mock_sale.save.assert_called_once()

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_patch_state_blocked_state(self, mock_get_object):
        """Test: intentar cambiar estado de venta bloqueada (entregada)"""
        mock_state = MagicMock()
        mock_state.name_state = 'entregada'

        mock_sale = MagicMock()
        mock_sale.state = mock_state
        mock_get_object.return_value = mock_sale

        url = reverse('sales-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('no se puede cambiar', response.data['message'].lower())
        self.assertIn('entregada', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_patch_state_anulada(self, mock_get_object):
        """Test: intentar cambiar estado de venta anulada"""
        mock_state = MagicMock()
        mock_state.name_state = 'anulada'

        mock_sale = MagicMock()
        mock_sale.state = mock_state
        mock_get_object.return_value = mock_sale

        url = reverse('sales-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('no se puede cambiar', response.data['message'].lower())
        self.assertIn('anulada', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_patch_state_cancelada(self, mock_get_object):
        """Test: intentar cambiar estado de venta cancelada"""
        mock_state = MagicMock()
        mock_state.name_state = 'cancelada'

        mock_sale = MagicMock()
        mock_sale.state = mock_state
        mock_get_object.return_value = mock_sale

        url = reverse('sales-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('no se puede cambiar', response.data['message'].lower())
        self.assertIn('cancelada', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_patch_state_missing_state(self, mock_get_object):
        """Test: patch_state sin enviar estado"""
        mock_state = MagicMock()
        mock_state.name_state = 'Pendiente'

        mock_sale = MagicMock()
        mock_sale.state = mock_state
        mock_get_object.return_value = mock_sale

        url = reverse('sales-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('necesitas enviar', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_patch_state_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en patch_state"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('sales-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Sales.views.SalesViewSets.get_object')
    def test_patch_state_exception(self, mock_get_object):
        """Test: excepcion generica en patch_state"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('sales-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA export_sales ====================

    @patch('api.Sales.models.Sales.objects.select_related')
    def test_export_sales_success(self, mock_select_related):
        """Test: exportar todas las ventas"""
        mock_queryset = MagicMock()
        mock_queryset.prefetch_related.return_value = mock_queryset
        mock_select_related.return_value = mock_queryset
        with patch('api.Sales.views.Export_sales_list') as mock_export:
            mock_export.return_value = Response({'message': 'Exportado'}, status=status.HTTP_200_OK)
            response = self.client.get(self.url_export_sales)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_select_related.assert_called_once_with('client', 'state')

    @patch('api.Sales.models.Sales.objects.select_related')
    def test_export_sales_exception(self, mock_select_related):
        """Test: excepcion en export_sales"""
        mock_select_related.side_effect = Exception('Export error')
        response = self.client.get(self.url_export_sales)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS DE METODOS HTTP ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar metodos HTTP no soportados"""
        response_post = self.client.post(self.url_get_sales, {})
        response_put = self.client.put(self.url_get_sales, {})
        response_delete = self.client.delete(self.url_get_sales)
        self.assertIn(response_post.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])

    def test_get_methods_for_post_endpoints(self):
        """Test: verificar que endpoints POST no aceptan GET"""
        url = reverse('sales-create-sale')
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])

        url = reverse('sales-delete-sale', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])


# =============================================================================
# TESTS PARA SalesDetailViewsets
# =============================================================================

class SalesDetailViewsetsTestCase(APITestCase):
    """Test cases para SalesDetailViewsets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = SalesDetailViewsets()
        self.assertEqual(viewset.queryset.model, SalesDetail)
        self.assertEqual(viewset.serializer_class, SalesDetailsSerializer)
        self.assertEqual(viewset.required_module, 'Ventas')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        expected_fields = ['sale', 'variant', 'quantity', 'unit_price', 'subtotal', 'creation_date']
        self.assertEqual(viewset.search_fields, expected_fields)

    # ==================== TESTS PARA get_sales_by_id (detalles) ====================

    @patch('api.Sales.models.SalesDetail.objects.filter')
    @patch('api.Sales.views.SalesDetailViewsets.get_serializer')
    def test_get_sales_by_id_success(self, mock_get_serializer, mock_filter):
        """Test: obtener detalles por ID de venta exitosamente"""
        mock_details = MagicMock()
        mock_details.exists.return_value = True
        mock_filter.return_value = mock_details
        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'sale': 1, 'variant': 1, 'quantity': 10, 'unit_price': 50.00},
        ]
        mock_get_serializer.return_value = mock_serializer
        url = reverse('sales-detail-get-sales-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalle de la venta')
        self.assertEqual(len(response.data['results']), 1)
        mock_filter.assert_called_once_with(sale=1)

    @patch('api.Sales.models.SalesDetail.objects.filter')
    def test_get_sales_by_id_empty(self, mock_filter):
        """Test: venta sin detalles (400)"""
        mock_details = MagicMock()
        mock_details.exists.return_value = False
        mock_filter.return_value = mock_details
        url = reverse('sales-detail-get-sales-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('no hay detalles', response.data['message'].lower())

    @patch('api.Sales.models.SalesDetail.objects.filter')
    def test_get_sales_by_id_exception(self, mock_filter):
        """Test: excepcion en get_sales_by_id"""
        mock_filter.side_effect = Exception('Database error')
        url = reverse('sales-detail-get-sales-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('database error', response.data['message'].lower())

    # ==================== TESTS PARA search_details ====================

    @patch('api.Sales.views.SalesDetailViewsets.filter_queryset')
    @patch('api.Sales.views.SalesDetailViewsets.get_queryset')
    @patch('api.Sales.views.SalesDetailViewsets.get_serializer')
    def test_search_details_success(self, mock_get_serializer, mock_get_queryset, mock_filter_queryset):
        """Test: buscar detalles con resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'quantity': 10}]
        mock_get_serializer.return_value = mock_serializer
        url = reverse('sales-detail-search-details')
        response = self.client.get(url, {'search': '10'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalles encontrados')

    @patch('api.Sales.views.SalesDetailViewsets.get_queryset')
    def test_search_details_exception(self, mock_get_queryset):
        """Test: excepcion en search_details"""
        mock_get_queryset.side_effect = Exception('Search error')
        url = reverse('sales-detail-search-details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS DE ModelViewSet CRUD ====================

    def test_list_sales_details(self):
        """Test: listar detalles (ModelViewSet list)"""
        with patch('api.Sales.views.SalesDetailViewsets.get_queryset') as mock_qs, \
             patch('api.Sales.views.SalesDetailViewsets.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_serializer = MagicMock()
            mock_serializer.data = [{'id': 1, 'quantity': 10}]
            mock_ser.return_value = mock_serializer
            response = self.client.get(reverse('sales-detail-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_sales_detail(self):
        """Test: crear detalle (ModelViewSet create)"""
        with patch('api.Sales.views.SalesDetailViewsets.get_serializer') as mock_ser:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1, 'sale': 1, 'variant': 1, 'quantity': 5}
            mock_ser.return_value = mock_serializer
            response = self.client.post(
                reverse('sales-detail-list'),
                {'sale': 1, 'variant': 1, 'quantity': 5, 'unit_price': 50.00},
                format='json'
            )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_sales_detail(self):
        """Test: actualizar detalle (ModelViewSet update)"""
        with patch('api.Sales.views.SalesDetailViewsets.get_object') as mock_obj, \
             patch('api.Sales.views.SalesDetailViewsets.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock(id=1)
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1, 'quantity': 15}
            mock_ser.return_value = mock_serializer
            response = self.client.put(
                reverse('sales-detail-detail', kwargs={'pk': 1}),
                {'quantity': 15},
                format='json'
            )
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_sales_detail(self):
        """Test: eliminar detalle (ModelViewSet destroy)"""
        with patch('api.Sales.views.SalesDetailViewsets.get_object') as mock_obj:
            mock_detail = MagicMock()
            mock_detail.delete = MagicMock()
            mock_obj.return_value = mock_detail
            response = self.client.delete(reverse('sales-detail-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

    def test_retrieve_sales_detail(self):
        """Test: obtener detalle por ID (ModelViewSet retrieve)"""
        with patch('api.Sales.views.SalesDetailViewsets.get_object') as mock_obj, \
             patch('api.Sales.views.SalesDetailViewsets.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock(id=1)
            mock_serializer = MagicMock()
            mock_serializer.data = {'id': 1, 'quantity': 10}
            mock_ser.return_value = mock_serializer
            response = self.client.get(reverse('sales-detail-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ==================== TESTS DE METODOS HTTP ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar metodos HTTP no soportados"""
        url = reverse('sales-detail-get-sales-by-id', kwargs={'pk': 1})
        response_post = self.client.post(url, {})
        response_put = self.client.put(url, {})
        response_delete = self.client.delete(url)
        self.assertIn(response_post.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])

# Create your tests here.
