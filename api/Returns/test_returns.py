from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status, filters
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock, ANY
from django.core.exceptions import MultipleObjectsReturned
from django.db.utils import IntegrityError
from rest_framework.response import Response

from api.Returns.models import Returns, ReturnDetail, Changes, ChangesDetails
from api.Returns.serializers import ReturnsSerializer, ReturnDetailSerializer, ChangesSerializer, ChangesDetailsSerializer
from api.Returns.views import ReturnsViewSets, ReturnDetailViewsets, ChangesViewSets, ChangesDetailViewsets
from api.Inventory.services import add_stock
from .services import Export_returns_list


User = get_user_model()


# =============================================================================
# TESTS PARA ReturnsViewSets
# =============================================================================

class ReturnsViewSetsTestCase(APITestCase):
    """Test cases para ReturnsViewSets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_returns = reverse('returns-get-returns')
        self.url_create_return = reverse('returns-create-return')
        self.url_search_returns = reverse('returns-search-returns')
        self.url_get_metrics = reverse('returns-get-metrics')
        self.url_export_all_returns = reverse('returns-export-all-returns')

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = ReturnsViewSets()
        self.assertEqual(viewset.queryset.model, Returns)
        self.assertEqual(viewset.serializer_class, ReturnsSerializer)
        self.assertEqual(viewset.required_module, 'Devoluciones')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        expected_fields = [
            'id_return', 'return_number', 'sale', 'return_date', 'reason',
            'state', 'total', 'balance_in_favor', 'difference_to_pay'
        ]
        self.assertEqual(viewset.search_fields, expected_fields)

    # ==================== TESTS PARA get_returns ====================

    @patch('api.Returns.views.ReturnsViewSets.get_queryset')
    @patch('api.Returns.views.ReturnsViewSets.get_serializer')
    def test_get_returns_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de devoluciones exitosamente"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_get_queryset.return_value = mock_queryset
        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'return_number': 'RET-001', 'total': 100.00},
            {'id': 2, 'return_number': 'RET-002', 'total': 200.00},
        ]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_returns)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'devoluciones obtenidas')
        self.assertEqual(len(response.data['results']), 2)

    @patch('api.Returns.views.ReturnsViewSets.get_queryset')
    def test_get_returns_empty(self, mock_get_queryset):
        """Test: obtener lista de devoluciones vacia (404)"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_get_queryset.return_value = mock_queryset
        response = self.client.get(self.url_get_returns)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existen', response.data['message'].lower())

    @patch('api.Returns.views.ReturnsViewSets.get_queryset')
    def test_get_returns_exception(self, mock_get_queryset):
        """Test: excepcion en get_returns"""
        mock_get_queryset.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_returns)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('database error', response.data['message'].lower())

    # ==================== TESTS PARA get_return_by_id ====================

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    @patch('api.Returns.views.ReturnsViewSets.get_serializer')
    def test_get_return_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener devolucion por ID exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'return_number': 'RET-001', 'total': 100.00}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('returns-get-return-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'devolucion obtenida')
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    def test_get_return_by_id_not_found(self, mock_get_object):
        """Test: devolucion no encontrada"""
        mock_get_object.side_effect = Returns.DoesNotExist("No existe")
        url = reverse('returns-get-return-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    def test_get_return_by_id_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('returns-get-return-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    def test_get_return_by_id_exception(self, mock_get_object):
        """Test: excepcion generica"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('returns-get-return-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA create_return ====================

    @patch('api.Returns.views.ReturnsViewSets.get_serializer')
    @patch('django.db.transaction.atomic')
    def test_create_return_success(self, mock_atomic, mock_get_serializer):
        """Test: crear devolucion exitosamente (201 Created)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'return_number': 'RET-001', 'total': 100.00}
        mock_get_serializer.return_value = mock_serializer
        data = {'return_number': 'RET-001', 'sale': 1, 'total': 100.00}
        response = self.client.post(self.url_create_return, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'devolucion creada exitosamente')
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Returns.views.ReturnsViewSets.get_serializer')
    @patch('django.db.transaction.atomic')
    def test_create_return_integrity_error(self, mock_atomic, mock_get_serializer):
        """Test: crear devolucion con IntegrityError"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer
        data = {'return_number': 'RET-001'}
        response = self.client.post(self.url_create_return, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('integridad', response.data['message'].lower())

    @patch('api.Returns.views.ReturnsViewSets.get_serializer')
    @patch('django.db.transaction.atomic')
    def test_create_return_exception(self, mock_atomic, mock_get_serializer):
        """Test: excepcion generica en create_return"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Unexpected error')
        mock_get_serializer.return_value = mock_serializer
        data = {'return_number': 'RET-001'}
        response = self.client.post(self.url_create_return, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('unexpected error', response.data['message'].lower())

    @patch('api.Returns.views.ReturnsViewSets.get_serializer')
    @patch('django.db.transaction.atomic')
    def test_create_return_validation_error(self, mock_atomic, mock_get_serializer):
        """Test: crear devolucion con ValidationError"""
        from rest_framework.exceptions import ValidationError
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'return_number': ['Requerido']})
        mock_get_serializer.return_value = mock_serializer
        data = {}
        response = self.client.post(self.url_create_return, data, format='json')
        # ValidationError no esta capturada, cae en Exception -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA delete_return ====================

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    @patch('api.Returns.views.add_stock')
    @patch('django.db.transaction.atomic')
    def test_delete_return_success(self, mock_atomic, mock_add_stock, mock_get_object):
        """Test: eliminar devolucion anulada exitosamente"""
        mock_state = MagicMock()
        mock_state.name_state = 'Anulado'

        mock_detail1 = MagicMock()
        mock_detail1.variant = MagicMock(id=1)
        mock_detail1.quantity = 5
        mock_detail2 = MagicMock()
        mock_detail2.variant = MagicMock(id=2)
        mock_detail2.quantity = 3

        mock_return = MagicMock()
        mock_return.state = mock_state
        mock_return.return_detail.all.return_value = [mock_detail1, mock_detail2]
        mock_return.delete = MagicMock()
        mock_get_object.return_value = mock_return

        url = reverse('returns-delete-return', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'devolucion eliminada exitosamente')
        mock_return.delete.assert_called_once()
        mock_add_stock.assert_any_call(mock_detail1.variant, 5)
        mock_add_stock.assert_any_call(mock_detail2.variant, 3)
        self.assertEqual(mock_add_stock.call_count, 2)

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_return_not_canceled(self, mock_atomic, mock_get_object):
        """Test: intentar eliminar devolucion no anulada"""
        mock_state = MagicMock()
        mock_state.name_state = 'Pendiente'

        mock_return = MagicMock()
        mock_return.state = mock_state
        mock_get_object.return_value = mock_return

        url = reverse('returns-delete-return', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('solo se pueden eliminar', response.data['message'].lower())

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_return_not_found(self, mock_atomic, mock_get_object):
        """Test: eliminar devolucion inexistente"""
        mock_get_object.side_effect = Returns.DoesNotExist("No existe")
        url = reverse('returns-delete-return', kwargs={'pk': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_return_multiple_objects(self, mock_atomic, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('returns-delete-return', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_return_exception(self, mock_atomic, mock_get_object):
        """Test: excepcion generica en delete_return"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('returns-delete-return', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA search_returns ====================

    @patch('api.Returns.views.ReturnsViewSets.filter_queryset')
    @patch('api.Returns.views.ReturnsViewSets.get_queryset')
    @patch('api.Returns.views.ReturnsViewSets.get_serializer')
    def test_search_returns_success(self, mock_get_serializer, mock_get_queryset, mock_filter_queryset):
        """Test: buscar devoluciones con resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'return_number': 'RET-001'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_search_returns, {'search': 'RET-001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'devoluciones obtenidas')

    @patch('api.Returns.views.ReturnsViewSets.get_queryset')
    def test_search_returns_exception(self, mock_get_queryset):
        """Test: excepcion en search_returns"""
        mock_get_queryset.side_effect = Exception('Search error')
        response = self.client.get(self.url_search_returns)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA get_metrics ====================

    @patch('api.Returns.models.Returns.objects.count')
    def test_get_metrics_success(self, mock_count):
        """Test: obtener metricas de devoluciones"""
        mock_count.return_value = 15
        response = self.client.get(self.url_get_metrics)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'metricas de devoluciones')
        self.assertEqual(response.data['metrics']['cantidad_devoluciones'], 15)

    @patch('api.Returns.models.Returns.objects.count')
    def test_get_metrics_zero(self, mock_count):
        """Test: metricas con cero devoluciones"""
        mock_count.return_value = 0
        response = self.client.get(self.url_get_metrics)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['metrics']['cantidad_devoluciones'], 0)

    @patch('api.Returns.models.Returns.objects.count')
    def test_get_metrics_exception(self, mock_count):
        """Test: excepcion en get_metrics"""
        mock_count.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_metrics)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('database error', response.data['message'].lower())

    # ==================== TESTS PARA export_all_returns ====================

    @patch('api.Returns.models.Returns.objects.select_related')
    def test_export_all_returns_success(self, mock_select_related):
        """Test: exportar todas las devoluciones"""
        mock_queryset = MagicMock()
        mock_queryset.prefetch_related.return_value = mock_queryset
        mock_select_related.return_value = mock_queryset
        with patch('api.Returns.views.Export_returns_list') as mock_export:
            mock_export.return_value = Response({'message': 'Exportado'}, status=status.HTTP_200_OK)
            response = self.client.get(self.url_export_all_returns)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_select_related.assert_called_once_with('sale', 'state')

    @patch('api.Returns.models.Returns.objects.select_related')
    def test_export_all_returns_exception(self, mock_select_related):
        """Test: excepcion en export_all_returns"""
        mock_select_related.side_effect = Exception('Export error')
        response = self.client.get(self.url_export_all_returns)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('export error', response.data['message'].lower())

    # ==================== TESTS PARA export_return_by_id ====================

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    @patch('api.Returns.models.Returns.objects.filter')
    def test_export_return_by_id_success(self, mock_filter, mock_get_object):
        """Test: exportar devolucion por ID"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_queryset = MagicMock()
        mock_queryset.select_related.return_value.prefetch_related.return_value = mock_queryset
        mock_filter.return_value = mock_queryset
        with patch('api.Returns.views.Export_returns_list') as mock_export:
            mock_export.return_value = Response({'message': 'Exportado'}, status=status.HTTP_200_OK)
            url = reverse('returns-export-return-by-id', kwargs={'pk': 1})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            mock_filter.assert_called_once_with(id_return=1)

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    def test_export_return_by_id_not_found(self, mock_get_object):
        """Test: exportar devolucion inexistente"""
        mock_get_object.side_effect = Returns.DoesNotExist("No existe")
        url = reverse('returns-export-return-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Returns.views.ReturnsViewSets.get_object')
    def test_export_return_by_id_exception(self, mock_get_object):
        """Test: excepcion en export_return_by_id"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('returns-export-return-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS DE METODOS HTTP ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar metodos HTTP no soportados"""
        response_post = self.client.post(self.url_get_returns, {})
        response_put = self.client.put(self.url_get_returns, {})
        response_delete = self.client.delete(self.url_get_returns)
        self.assertIn(response_post.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])


# =============================================================================
# TESTS PARA ReturnDetailViewsets
# =============================================================================

class ReturnDetailViewsetsTestCase(APITestCase):
    """Test cases para ReturnDetailViewsets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = ReturnDetailViewsets()
        self.assertEqual(viewset.queryset.model, ReturnDetail)
        self.assertEqual(viewset.serializer_class, ReturnDetailSerializer)
        self.assertEqual(viewset.required_module, 'Devoluciones')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        expected_fields = ['return_id', 'variant', 'quantity', 'subtotal']
        self.assertEqual(viewset.search_fields, expected_fields)

    # ==================== TESTS PARA get_returns_by_id ====================

    @patch('api.Returns.models.ReturnDetail.objects.filter')
    @patch('api.Returns.views.ReturnDetailViewsets.get_serializer')
    def test_get_returns_by_id_success(self, mock_get_serializer, mock_filter):
        """Test: obtener detalles por ID de devolucion"""
        mock_details = MagicMock()
        mock_details.exists.return_value = True
        mock_filter.return_value = mock_details
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'return_id': 1, 'variant': 1, 'quantity': 5}]
        mock_get_serializer.return_value = mock_serializer
        url = reverse('return-detail-get-returns-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalle de la devolucion')
        self.assertEqual(len(response.data['results']), 1)
        mock_filter.assert_called_once_with(return_id=1)

    @patch('api.Returns.models.ReturnDetail.objects.filter')
    def test_get_returns_by_id_empty(self, mock_filter):
        """Test: devolucion sin detalles (400)"""
        mock_details = MagicMock()
        mock_details.exists.return_value = False
        mock_filter.return_value = mock_details
        url = reverse('return-detail-get-returns-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('no hay detalles', response.data['message'].lower())

    @patch('api.Returns.models.ReturnDetail.objects.filter')
    def test_get_returns_by_id_exception(self, mock_filter):
        """Test: excepcion en get_returns_by_id"""
        mock_filter.side_effect = Exception('Database error')
        url = reverse('return-detail-get-returns-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA search_details ====================

    @patch('api.Returns.views.ReturnDetailViewsets.filter_queryset')
    @patch('api.Returns.views.ReturnDetailViewsets.get_queryset')
    @patch('api.Returns.views.ReturnDetailViewsets.get_serializer')
    def test_search_details_success(self, mock_get_serializer, mock_get_queryset, mock_filter_queryset):
        """Test: buscar detalles con resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'quantity': 5}]
        mock_get_serializer.return_value = mock_serializer
        url = reverse('return-detail-search-details')
        response = self.client.get(url, {'search': '5'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalles encontrados')

    @patch('api.Returns.views.ReturnDetailViewsets.get_queryset')
    def test_search_details_exception(self, mock_get_queryset):
        """Test: excepcion en search_details"""
        mock_get_queryset.side_effect = Exception('Search error')
        url = reverse('return-detail-search-details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS DE ModelViewSet CRUD ====================

    def test_list_return_details(self):
        """Test: listar detalles (ModelViewSet list)"""
        with patch('api.Returns.views.ReturnDetailViewsets.get_queryset') as mock_qs, \
             patch('api.Returns.views.ReturnDetailViewsets.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_serializer = MagicMock()
            mock_serializer.data = [{'id': 1, 'quantity': 5}]
            mock_ser.return_value = mock_serializer
            response = self.client.get(reverse('return-detail-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_return_detail(self):
        """Test: crear detalle (ModelViewSet create)"""
        with patch('api.Returns.views.ReturnDetailViewsets.get_serializer') as mock_ser:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1, 'quantity': 5}
            mock_ser.return_value = mock_serializer
            response = self.client.post(reverse('return-detail-list'), {'return_id': 1, 'variant': 1, 'quantity': 5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_return_detail(self):
        """Test: actualizar detalle (ModelViewSet update)"""
        with patch('api.Returns.views.ReturnDetailViewsets.get_object') as mock_obj, \
             patch('api.Returns.views.ReturnDetailViewsets.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock(id=1)
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1, 'quantity': 10}
            mock_ser.return_value = mock_serializer
            response = self.client.put(reverse('return-detail-detail', kwargs={'pk': 1}), {'quantity': 10}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_return_detail(self):
        """Test: eliminar detalle (ModelViewSet destroy)"""
        with patch('api.Returns.views.ReturnDetailViewsets.get_object') as mock_obj:
            mock_detail = MagicMock()
            mock_detail.delete = MagicMock()
            mock_obj.return_value = mock_detail
            response = self.client.delete(reverse('return-detail-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)


# =============================================================================
# TESTS PARA ChangesViewSets
# =============================================================================

class ChangesViewSetsTestCase(APITestCase):
    """Test cases para ChangesViewSets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_changes = reverse('changes-get-changes')
        self.url_create_change = reverse('changes-create-change')
        self.url_search_changes = reverse('changes-search-changes')
        self.url_get_metrics = reverse('changes-get-metrics')

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = ChangesViewSets()
        self.assertEqual(viewset.queryset.model, Changes)
        self.assertEqual(viewset.serializer_class, ChangesSerializer)
        self.assertEqual(viewset.required_module, 'Devoluciones')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        expected_fields = [
            'id_change', 'change_number', 'sale', 'reason_of_change',
            'state', 'stock_applied', 'return_applied'
        ]
        self.assertEqual(viewset.search_fields, expected_fields)

    # ==================== TESTS PARA get_changes ====================

    @patch('api.Returns.views.ChangesViewSets.get_queryset')
    @patch('api.Returns.views.ChangesViewSets.get_serializer')
    def test_get_changes_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de cambios exitosamente"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_get_queryset.return_value = mock_queryset
        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'change_number': 'CHG-001', 'reason_of_change': 'Defecto'},
        ]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_changes)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'cambios obtenidos')
        self.assertEqual(len(response.data['results']), 1)

    @patch('api.Returns.views.ChangesViewSets.get_queryset')
    def test_get_changes_empty(self, mock_get_queryset):
        """Test: obtener lista de cambios vacia (404)"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_get_queryset.return_value = mock_queryset
        response = self.client.get(self.url_get_changes)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existen', response.data['message'].lower())

    @patch('api.Returns.views.ChangesViewSets.get_queryset')
    def test_get_changes_exception(self, mock_get_queryset):
        """Test: excepcion en get_changes"""
        mock_get_queryset.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_changes)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA get_change_by_id ====================

    @patch('api.Returns.views.ChangesViewSets.get_object')
    @patch('api.Returns.views.ChangesViewSets.get_serializer')
    def test_get_change_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener cambio por ID exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'change_number': 'CHG-001'}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('changes-get-change-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'cambio obtenido')
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.Returns.views.ChangesViewSets.get_object')
    def test_get_change_by_id_not_found(self, mock_get_object):
        """Test: cambio no encontrado"""
        mock_get_object.side_effect = Changes.DoesNotExist("No existe")
        url = reverse('changes-get-change-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Returns.views.ChangesViewSets.get_object')
    def test_get_change_by_id_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('changes-get-change-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Returns.views.ChangesViewSets.get_object')
    def test_get_change_by_id_exception(self, mock_get_object):
        """Test: excepcion generica"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('changes-get-change-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA create_change ====================

    @patch('api.Returns.views.ChangesViewSets.get_serializer')
    @patch('django.db.transaction.atomic')
    def test_create_change_success(self, mock_atomic, mock_get_serializer):
        """Test: crear cambio exitosamente (201 Created)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'change_number': 'CHG-001'}
        mock_get_serializer.return_value = mock_serializer
        data = {'change_number': 'CHG-001', 'sale': 1, 'reason_of_change': 'Defecto'}
        response = self.client.post(self.url_create_change, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'cambio creado exitosamente')
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Returns.views.ChangesViewSets.get_serializer')
    @patch('django.db.transaction.atomic')
    def test_create_change_integrity_error(self, mock_atomic, mock_get_serializer):
        """Test: crear cambio con IntegrityError"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer
        data = {'change_number': 'CHG-001'}
        response = self.client.post(self.url_create_change, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('integridad', response.data['message'].lower())

    @patch('api.Returns.views.ChangesViewSets.get_serializer')
    @patch('django.db.transaction.atomic')
    def test_create_change_exception(self, mock_atomic, mock_get_serializer):
        """Test: excepcion generica en create_change"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Unexpected error')
        mock_get_serializer.return_value = mock_serializer
        data = {'change_number': 'CHG-001'}
        response = self.client.post(self.url_create_change, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA delete_change ====================

    @patch('api.Returns.views.ChangesViewSets.get_object')
    @patch('api.Returns.views.add_stock')
    @patch('django.db.transaction.atomic')
    def test_delete_change_success_with_stock(self, mock_atomic, mock_add_stock, mock_get_object):
        """Test: eliminar cambio anulado con stock aplicado"""
        mock_state = MagicMock()
        mock_state.name_state = 'Anulado'

        mock_detail = MagicMock()
        mock_detail.variant_delivered = MagicMock(id=1)

        mock_change = MagicMock()
        mock_change.state = mock_state
        mock_change.stock_applied = True
        mock_change.change_detail.all.return_value = [mock_detail]
        mock_change.delete = MagicMock()
        mock_get_object.return_value = mock_change

        url = reverse('changes-delete-change', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'cambio eliminado exitosamente')
        mock_change.delete.assert_called_once()
        mock_add_stock.assert_called_once_with(mock_detail.variant_delivered, 1)

    @patch('api.Returns.views.ChangesViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_change_success_without_stock(self, mock_atomic, mock_get_object):
        """Test: eliminar cambio anulado sin stock aplicado"""
        mock_state = MagicMock()
        mock_state.name_state = 'Anulado'

        mock_change = MagicMock()
        mock_change.state = mock_state
        mock_change.stock_applied = False
        mock_change.change_detail.all.return_value = []
        mock_change.delete = MagicMock()
        mock_get_object.return_value = mock_change

        url = reverse('changes-delete-change', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_change.delete.assert_called_once()

    @patch('api.Returns.views.ChangesViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_change_not_canceled(self, mock_atomic, mock_get_object):
        """Test: intentar eliminar cambio no anulado"""
        mock_state = MagicMock()
        mock_state.name_state = 'Pendiente'

        mock_change = MagicMock()
        mock_change.state = mock_state
        mock_get_object.return_value = mock_change

        url = reverse('changes-delete-change', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('solo se pueden eliminar', response.data['message'].lower())

    @patch('api.Returns.views.ChangesViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_change_not_found(self, mock_atomic, mock_get_object):
        """Test: eliminar cambio inexistente"""
        mock_get_object.side_effect = Changes.DoesNotExist("No existe")
        url = reverse('changes-delete-change', kwargs={'pk': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Returns.views.ChangesViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_change_multiple_objects(self, mock_atomic, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('changes-delete-change', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Returns.views.ChangesViewSets.get_object')
    @patch('django.db.transaction.atomic')
    def test_delete_change_exception(self, mock_atomic, mock_get_object):
        """Test: excepcion generica en delete_change"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('changes-delete-change', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA search_changes ====================

    @patch('api.Returns.views.ChangesViewSets.filter_queryset')
    @patch('api.Returns.views.ChangesViewSets.get_queryset')
    @patch('api.Returns.views.ChangesViewSets.get_serializer')
    def test_search_changes_success(self, mock_get_serializer, mock_get_queryset, mock_filter_queryset):
        """Test: buscar cambios con resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'change_number': 'CHG-001'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_search_changes, {'search': 'CHG-001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'cambios obtenidos')

    @patch('api.Returns.views.ChangesViewSets.get_queryset')
    def test_search_changes_exception(self, mock_get_queryset):
        """Test: excepcion en search_changes"""
        mock_get_queryset.side_effect = Exception('Search error')
        response = self.client.get(self.url_search_changes)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA get_metrics ====================

    @patch('api.Returns.models.Changes.objects.count')
    def test_get_metrics_success(self, mock_count):
        """Test: obtener metricas de cambios"""
        mock_count.return_value = 10
        response = self.client.get(self.url_get_metrics)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'metricas de cambios')
        self.assertEqual(response.data['metrics']['cantidad_cambios'], 10)

    @patch('api.Returns.models.Changes.objects.count')
    def test_get_metrics_zero(self, mock_count):
        """Test: metricas con cero cambios"""
        mock_count.return_value = 0
        response = self.client.get(self.url_get_metrics)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['metrics']['cantidad_cambios'], 0)

    @patch('api.Returns.models.Changes.objects.count')
    def test_get_metrics_exception(self, mock_count):
        """Test: excepcion en get_metrics"""
        mock_count.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_metrics)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS DE METODOS HTTP ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar metodos HTTP no soportados"""
        response_post = self.client.post(self.url_get_changes, {})
        response_put = self.client.put(self.url_get_changes, {})
        response_delete = self.client.delete(self.url_get_changes)
        self.assertIn(response_post.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])


# =============================================================================
# TESTS PARA ChangesDetailViewsets
# =============================================================================

class ChangesDetailViewsetsTestCase(APITestCase):
    """Test cases para ChangesDetailViewsets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = ChangesDetailViewsets()
        self.assertEqual(viewset.queryset.model, ChangesDetails)
        self.assertEqual(viewset.serializer_class, ChangesDetailsSerializer)
        self.assertEqual(viewset.required_module, 'Devoluciones')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        expected_fields = ['change', 'variant_returned', 'variant_delivered']
        self.assertEqual(viewset.search_fields, expected_fields)

    # ==================== TESTS PARA get_changes_by_id ====================

    @patch('api.Returns.models.ChangesDetails.objects.filter')
    @patch('api.Returns.views.ChangesDetailViewsets.get_serializer')
    def test_get_changes_by_id_success(self, mock_get_serializer, mock_filter):
        """Test: obtener detalles por ID de cambio"""
        mock_details = MagicMock()
        mock_details.exists.return_value = True
        mock_filter.return_value = mock_details
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'change': 1, 'variant_returned': 1, 'variant_delivered': 2}]
        mock_get_serializer.return_value = mock_serializer
        url = reverse('changes-detail-get-changes-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalle del cambio')
        self.assertEqual(len(response.data['results']), 1)
        mock_filter.assert_called_once_with(change=1)

    @patch('api.Returns.models.ChangesDetails.objects.filter')
    def test_get_changes_by_id_empty(self, mock_filter):
        """Test: cambio sin detalles (400)"""
        mock_details = MagicMock()
        mock_details.exists.return_value = False
        mock_filter.return_value = mock_details
        url = reverse('changes-detail-get-changes-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('no hay detalles', response.data['message'].lower())

    @patch('api.Returns.models.ChangesDetails.objects.filter')
    def test_get_changes_by_id_exception(self, mock_filter):
        """Test: excepcion en get_changes_by_id"""
        mock_filter.side_effect = Exception('Database error')
        url = reverse('changes-detail-get-changes-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA search_details ====================

    @patch('api.Returns.views.ChangesDetailViewsets.filter_queryset')
    @patch('api.Returns.views.ChangesDetailViewsets.get_queryset')
    @patch('api.Returns.views.ChangesDetailViewsets.get_serializer')
    def test_search_details_success(self, mock_get_serializer, mock_get_queryset, mock_filter_queryset):
        """Test: buscar detalles con resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'variant_returned': 1}]
        mock_get_serializer.return_value = mock_serializer
        url = reverse('changes-detail-search-details')
        response = self.client.get(url, {'search': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalles encontrados')

    @patch('api.Returns.views.ChangesDetailViewsets.get_queryset')
    def test_search_details_exception(self, mock_get_queryset):
        """Test: excepcion en search_details"""
        mock_get_queryset.side_effect = Exception('Search error')
        url = reverse('changes-detail-search-details')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS DE ModelViewSet CRUD ====================

    def test_list_changes_details(self):
        """Test: listar detalles (ModelViewSet list)"""
        with patch('api.Returns.views.ChangesDetailViewsets.get_queryset') as mock_qs, \
             patch('api.Returns.views.ChangesDetailViewsets.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_serializer = MagicMock()
            mock_serializer.data = [{'id': 1, 'variant_returned': 1}]
            mock_ser.return_value = mock_serializer
            response = self.client.get(reverse('changes-detail-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_changes_detail(self):
        """Test: crear detalle (ModelViewSet create)"""
        with patch('api.Returns.views.ChangesDetailViewsets.get_serializer') as mock_ser:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1, 'change': 1, 'variant_returned': 1, 'variant_delivered': 2}
            mock_ser.return_value = mock_serializer
            response = self.client.post(reverse('changes-detail-list'), {'change': 1, 'variant_returned': 1, 'variant_delivered': 2}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_changes_detail(self):
        """Test: actualizar detalle (ModelViewSet update)"""
        with patch('api.Returns.views.ChangesDetailViewsets.get_object') as mock_obj, \
             patch('api.Returns.views.ChangesDetailViewsets.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock(id=1)
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1, 'variant_returned': 1, 'variant_delivered': 3}
            mock_ser.return_value = mock_serializer
            response = self.client.put(reverse('changes-detail-detail', kwargs={'pk': 1}), {'variant_delivered': 3}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_changes_detail(self):
        """Test: eliminar detalle (ModelViewSet destroy)"""
        with patch('api.Returns.views.ChangesDetailViewsets.get_object') as mock_obj:
            mock_detail = MagicMock()
            mock_detail.delete = MagicMock()
            mock_obj.return_value = mock_detail
            response = self.client.delete(reverse('changes-detail-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

# Create your tests here.
