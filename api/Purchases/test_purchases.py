from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status, filters
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock, ANY
from django.core.exceptions import MultipleObjectsReturned
from django.db.utils import IntegrityError
from rest_framework.response import Response

from api.Purchases.models import Purchases, PurchaseDetail, Iva
from api.Purchases.serializers import PurchasesSerializer, PurchaseDetailSerializer, IvaSerializer
from api.Purchases.views import PurchasesViewSet, PurchaseDetailViewSet, IvaViewSets
from api.Inventory.services import out_stock


User = get_user_model()


# =============================================================================
# TESTS PARA PurchasesViewSet
# =============================================================================

class PurchasesViewSetTestCase(APITestCase):
    """Test cases para PurchasesViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_purchases = reverse('purchases-get-purchases')
        self.url_create_purchase = reverse('purchases-create-purchase')
        self.url_search_purchases = reverse('purchases-search-purchases')
        self.url_export_purchases = reverse('purchases-export-purchases')

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = PurchasesViewSet()
        self.assertEqual(viewset.queryset.model, Purchases)
        self.assertEqual(viewset.serializer_class, PurchasesSerializer)
        self.assertEqual(viewset.required_module, 'Compras')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        expected_fields = [
            'purchase_number', 'provider__name', 'state__name',
            'observations', 'total', 'subtotal', 'iva',
        ]
        self.assertEqual(viewset.search_fields, expected_fields)

    # ==================== TESTS PARA get_purchases ====================

    @patch('api.Purchases.views.PurchasesViewSet.get_queryset')
    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_get_purchases_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de compras exitosamente"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_get_queryset.return_value = mock_queryset
        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'purchase_number': 'COMP-001', 'total': 1000.00},
            {'id': 2, 'purchase_number': 'COMP-002', 'total': 2000.00},
        ]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_purchases)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'compras obtenidas')
        self.assertEqual(len(response.data['results']), 2)

    @patch('api.Purchases.views.PurchasesViewSet.get_queryset')
    def test_get_purchases_empty(self, mock_get_queryset):
        """Test: obtener lista de compras vacia"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_get_queryset.return_value = mock_queryset
        response = self.client.get(self.url_get_purchases)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], [])

    @patch('api.Purchases.views.PurchasesViewSet.get_queryset')
    def test_get_purchases_exception(self, mock_get_queryset):
        """Test: excepcion en get_purchases"""
        mock_get_queryset.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_purchases)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('database error', response.data['message'].lower())

    # ==================== TESTS PARA get_purchase_by_id ====================

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_get_purchase_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener compra por ID exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'purchase_number': 'COMP-001', 'total': 1000.00}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('purchases-get-purchase-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'compra obtenida')
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_get_purchase_by_id_not_found(self, mock_get_object):
        """Test: compra no encontrada"""
        mock_get_object.side_effect = Purchases.DoesNotExist("No existe")
        url = reverse('purchases-get-purchase-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no encontrada', response.data['message'].lower())

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_get_purchase_by_id_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('purchases-get-purchase-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_get_purchase_by_id_exception(self, mock_get_object):
        """Test: excepcion generica"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('purchases-get-purchase-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA create_purchase ====================

    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_create_purchase_success(self, mock_get_serializer):
        """Test: crear compra exitosamente (201 Created)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'purchase_number': 'COMP-001', 'total': 1000.00}
        mock_get_serializer.return_value = mock_serializer
        data = {'purchase_number': 'COMP-001', 'provider': 1, 'total': 1000.00}
        response = self.client.post(self.url_create_purchase, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'compra creada exitosamente')
        self.assertIn('object', response.data)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_create_purchase_validation_error(self, mock_get_serializer):
        """Test: crear compra con datos invalidos (ValidationError)"""
        from rest_framework.exceptions import ValidationError
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'purchase_number': ['Requerido']})
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_purchase, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_create_purchase_integrity_error(self, mock_get_serializer):
        """Test: crear compra con IntegrityError"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer
        data = {'purchase_number': 'COMP-001'}
        response = self.client.post(self.url_create_purchase, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('integridad', response.data['message'].lower())

    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_create_purchase_exception(self, mock_get_serializer):
        """Test: excepcion generica en create_purchase"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Unexpected error')
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_purchase, {'purchase_number': 'COMP-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA update_purchase ====================

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_update_purchase_success(self, mock_get_serializer, mock_get_object):
        """Test: actualizar compra exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'purchase_number': 'COMP-001-UPD', 'total': 1500.00}
        mock_get_serializer.return_value = mock_serializer
        data = {'purchase_number': 'COMP-001-UPD', 'total': 1500.00}
        url = reverse('purchases-update-purchase', kwargs={'pk': 1})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'compra actualizada exitosamente')
        self.assertIn('object', response.data)

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_update_purchase_not_found(self, mock_get_object):
        """Test: actualizar compra que no existe"""
        mock_get_object.side_effect = Purchases.DoesNotExist("No existe")
        url = reverse('purchases-update-purchase', kwargs={'pk': 999})
        response = self.client.put(url, {'purchase_number': 'COMP-999'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no encontrada', response.data['message'].lower())

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_update_purchase_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('purchases-update-purchase', kwargs={'pk': 1})
        response = self.client.put(url, {'purchase_number': 'COMP-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_update_purchase_exception(self, mock_get_object):
        """Test: excepcion generica en update_purchase"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('purchases-update-purchase', kwargs={'pk': 1})
        response = self.client.put(url, {'purchase_number': 'COMP-001'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA patch_state ====================

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_patch_state_cancel_true(self, mock_get_serializer, mock_get_object):
        """Test: cancelar compra (canceled=True)"""
        mock_purchase = MagicMock()
        mock_purchase.canceled = False
        mock_purchase.save = MagicMock()
        mock_get_object.return_value = mock_purchase
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'canceled': True}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('purchases-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'canceled': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'estado actualizado')
        self.assertTrue(mock_purchase.canceled)
        mock_purchase.save.assert_called_once()

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_patch_state_cancel_false(self, mock_get_serializer, mock_get_object):
        """Test: des-cancelar compra (canceled=False)"""
        mock_purchase = MagicMock()
        mock_purchase.canceled = True
        mock_purchase.save = MagicMock()
        mock_get_object.return_value = mock_purchase
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'canceled': False}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('purchases-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'canceled': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertFalse(mock_purchase.canceled)

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_patch_state_cancel_string_true(self, mock_get_serializer, mock_get_object):
        """Test: cancelar compra con string 'true'"""
        mock_purchase = MagicMock()
        mock_purchase.canceled = False
        mock_purchase.save = MagicMock()
        mock_get_object.return_value = mock_purchase
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'canceled': True}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('purchases-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'canceled': 'true'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_purchase.canceled)

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_patch_state_cancel_string_one(self, mock_get_serializer, mock_get_object):
        """Test: cancelar compra con string '1'"""
        mock_purchase = MagicMock()
        mock_purchase.canceled = False
        mock_purchase.save = MagicMock()
        mock_get_object.return_value = mock_purchase
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'canceled': True}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('purchases-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'canceled': '1'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(mock_purchase.canceled)

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_patch_state_cancel_string_false(self, mock_get_serializer, mock_get_object):
        """Test: des-cancelar compra con string 'false'"""
        mock_purchase = MagicMock()
        mock_purchase.canceled = True
        mock_purchase.save = MagicMock()
        mock_get_object.return_value = mock_purchase
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'canceled': False}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('purchases-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'canceled': 'false'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(mock_purchase.canceled)

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_patch_state_not_found(self, mock_get_object):
        """Test: patch_state en compra inexistente"""
        mock_get_object.side_effect = Purchases.DoesNotExist("No existe")
        url = reverse('purchases-patch-state', kwargs={'pk': 999})
        response = self.client.patch(url, {'canceled': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_patch_state_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en patch_state"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('purchases-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'canceled': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_patch_state_exception(self, mock_get_object):
        """Test: excepcion generica en patch_state"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('purchases-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'canceled': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA get_purchase_by_provider ====================

    @patch('api.Purchases.models.Purchases.objects.filter')
    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_get_purchase_by_provider_success(self, mock_get_serializer, mock_filter):
        """Test: obtener compras por proveedor exitosamente"""
        mock_purchases = MagicMock()
        mock_filter.return_value = mock_purchases
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'purchase_number': 'COMP-001', 'provider': 1}]
        mock_get_serializer.return_value = mock_serializer
        url = reverse('purchases-get-purchase-by-provider')
        response = self.client.get(url, {'provider': '1'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['message'], 'compras obtenidas')
        mock_filter.assert_called_once_with(provider='1')

    @patch('api.Purchases.models.Purchases.objects.filter')
    def test_get_purchase_by_provider_exception(self, mock_filter):
        """Test: excepcion en get_purchase_by_provider"""
        mock_filter.side_effect = Exception('Database error')
        url = reverse('purchases-get-purchase-by-provider')
        response = self.client.get(url, {'provider': '1'})
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    def test_get_purchase_by_provider_missing_param(self):
        """Test: obtener compras sin parametro provider"""
        url = reverse('purchases-get-purchase-by-provider')
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA delete_purchase ====================

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_delete_purchase_success_canceled(self, mock_get_object):
        """Test: eliminar compra anulada exitosamente"""
        mock_detail1 = MagicMock()
        mock_detail1.variant = MagicMock()
        mock_detail1.quantity = 10
        mock_detail2 = MagicMock()
        mock_detail2.variant = MagicMock()
        mock_detail2.quantity = 5

        mock_purchase = MagicMock()
        mock_purchase.canceled = True
        mock_purchase.delete = MagicMock()
        mock_purchase.detail_purchase.all.return_value = [mock_detail1, mock_detail2]
        mock_get_object.return_value = mock_purchase

        with patch('api.Purchases.views.out_stock') as mock_out_stock:
            url = reverse('purchases-delete-purchase', kwargs={'pk': 1})
            response = self.client.delete(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)
            self.assertTrue(response.data['success'])
            self.assertIn('eliminada', response.data['message'].lower())
            mock_purchase.delete.assert_called_once()
            self.assertEqual(mock_out_stock.call_count, 2)
            mock_out_stock.assert_any_call(mock_detail1.variant, 10)
            mock_out_stock.assert_any_call(mock_detail2.variant, 5)

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_delete_purchase_not_canceled(self, mock_get_object):
        """Test: intentar eliminar compra no anulada"""
        mock_purchase = MagicMock()
        mock_purchase.canceled = False
        mock_get_object.return_value = mock_purchase
        url = reverse('purchases-delete-purchase', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('solo se pueden eliminar', response.data['message'].lower())

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_delete_purchase_not_found(self, mock_get_object):
        """Test: eliminar compra inexistente"""
        mock_get_object.side_effect = Purchases.DoesNotExist("No existe")
        url = reverse('purchases-delete-purchase', kwargs={'pk': 999})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no encontrada', response.data['message'].lower())

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_delete_purchase_integrity_error(self, mock_get_object):
        """Test: eliminar compra con IntegrityError"""
        mock_purchase = MagicMock()
        mock_purchase.canceled = True
        mock_purchase.detail_purchase.all.return_value = []
        mock_purchase.delete.side_effect = IntegrityError("Foreign key constraint")
        mock_get_object.return_value = mock_purchase
        url = reverse('purchases-delete-purchase', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('integridad', response.data['message'].lower())

    @patch('api.Purchases.views.PurchasesViewSet.get_object')
    def test_delete_purchase_exception(self, mock_get_object):
        """Test: excepcion generica en delete_purchase"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('purchases-delete-purchase', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA search_purchases ====================

    @patch('api.Purchases.views.PurchasesViewSet.filter_queryset')
    @patch('api.Purchases.views.PurchasesViewSet.get_queryset')
    @patch('api.Purchases.views.PurchasesViewSet.get_serializer')
    def test_search_purchases_success(self, mock_get_serializer, mock_get_queryset, mock_filter_queryset):
        """Test: buscar compras con resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'purchase_number': 'COMP-001'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_search_purchases, {'search': 'COMP-001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'resultados obtenidos')

    @patch('api.Purchases.views.PurchasesViewSet.filter_queryset')
    @patch('api.Purchases.views.PurchasesViewSet.get_queryset')
    def test_search_purchases_empty(self, mock_get_queryset, mock_filter_queryset):
        """Test: buscar compras sin resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = False
        mock_filter_queryset.return_value = mock_filtered
        response = self.client.get(self.url_search_purchases, {'search': 'XYZ999'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'sin resultados')
        self.assertEqual(response.data['results'], [])

    @patch('api.Purchases.views.PurchasesViewSet.get_queryset')
    def test_search_purchases_exception(self, mock_get_queryset):
        """Test: excepcion en search_purchases"""
        mock_get_queryset.side_effect = Exception('Search error')
        response = self.client.get(self.url_search_purchases)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA export_purchases ====================

    @patch('api.Purchases.views.PurchasesViewSet.get_queryset')
    def test_export_purchases_success(self, mock_get_queryset):
        mock_queryset = MagicMock()
        mock_queryset.select_related.return_value.prefetch_related.return_value = mock_queryset
        mock_get_queryset.return_value = mock_queryset
        with patch('api.Purchases.views.Export_purchases_list') as mock_export:
            mock_export.return_value = Response({'message': 'Exportado'}, status=status.HTTP_200_OK)
            response = self.client.get(self.url_export_purchases)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.Purchases.views.PurchasesViewSet.get_queryset')
    def test_export_purchases_exception(self, mock_get_queryset):
        mock_get_queryset.side_effect = Exception('Export error')
        response = self.client.get(self.url_export_purchases)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS DE METODOS HTTP ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar metodos HTTP no soportados"""
        response_post = self.client.post(self.url_get_purchases, {})
        response_put = self.client.put(self.url_get_purchases, {})
        response_delete = self.client.delete(self.url_get_purchases)
        self.assertIn(response_post.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])


# =============================================================================
# TESTS PARA PurchaseDetailViewSet
# =============================================================================

class PurchaseDetailViewSetTestCase(APITestCase):
    """Test cases para PurchaseDetailViewSet"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_details = reverse('purchase-detail-get-details')
        self.url_search_details = reverse('purchase-detail-search-details')

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = PurchaseDetailViewSet()
        self.assertEqual(viewset.queryset.model, PurchaseDetail)
        self.assertEqual(viewset.serializer_class, PurchaseDetailSerializer)
        self.assertEqual(viewset.required_module, 'Compras')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        expected_fields = [
            'purchase__purchase_number', 'variant__sku', 'variant__product__name',
            'quantity', 'purchase_price', 'sales_price', 'subtotal',
        ]
        self.assertEqual(viewset.search_fields, expected_fields)

    # ==================== TESTS PARA get_details ====================

    @patch('api.Purchases.views.PurchaseDetailViewSet.get_queryset')
    @patch('api.Purchases.views.PurchaseDetailViewSet.get_serializer')
    def test_get_details_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de detalles exitosamente"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_get_queryset.return_value = mock_queryset
        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'purchase': 1, 'variant': 1, 'quantity': 10},
        ]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_details)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalles obtenidos')
        self.assertEqual(len(response.data['results']), 1)

    @patch('api.Purchases.views.PurchaseDetailViewSet.get_queryset')
    def test_get_details_empty(self, mock_get_queryset):
        """Test: obtener lista de detalles vacia"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_get_queryset.return_value = mock_queryset
        response = self.client.get(self.url_get_details)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], [])

    @patch('api.Purchases.views.PurchaseDetailViewSet.get_queryset')
    def test_get_details_exception(self, mock_get_queryset):
        """Test: excepcion en get_details"""
        mock_get_queryset.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_details)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA get_detail_by_id ====================

    @patch('api.Purchases.views.PurchaseDetailViewSet.get_object')
    @patch('api.Purchases.views.PurchaseDetailViewSet.get_serializer')
    def test_get_detail_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener detalle por ID exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'purchase': 1, 'variant': 1, 'quantity': 10}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('purchase-detail-get-detail-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalle obtenido')
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.Purchases.views.PurchaseDetailViewSet.get_object')
    def test_get_detail_by_id_not_found(self, mock_get_object):
        """Test: detalle no encontrado"""
        mock_get_object.side_effect = PurchaseDetail.DoesNotExist("No existe")
        url = reverse('purchase-detail-get-detail-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no encontrado', response.data['message'].lower())

    @patch('api.Purchases.views.PurchaseDetailViewSet.get_object')
    def test_get_detail_by_id_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('purchase-detail-get-detail-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Purchases.views.PurchaseDetailViewSet.get_object')
    def test_get_detail_by_id_exception(self, mock_get_object):
        """Test: excepcion generica"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('purchase-detail-get-detail-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA get_details_by_purchase ====================

    @patch('api.Purchases.models.PurchaseDetail.objects.filter')
    @patch('api.Purchases.views.PurchaseDetailViewSet.get_serializer')
    def test_get_details_by_purchase_success(self, mock_get_serializer, mock_filter):
        """Test: obtener detalles por compra exitosamente"""
        mock_details = MagicMock()
        mock_details.exists.return_value = True
        mock_filter.return_value = mock_details
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'purchase': 1, 'quantity': 10}]
        mock_get_serializer.return_value = mock_serializer
        url = reverse('purchase-detail-get-details-by-purchase', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'detalles obtenidos')
        mock_filter.assert_called_once_with(purchase=1)

    @patch('api.Purchases.models.PurchaseDetail.objects.filter')
    def test_get_details_by_purchase_empty(self, mock_filter):
        """Test: compra sin detalles"""
        mock_details = MagicMock()
        mock_details.exists.return_value = False
        mock_filter.return_value = mock_details
        url = reverse('purchase-detail-get-details-by-purchase', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], [])
        self.assertIn('no tiene detalles', response.data['message'].lower())

    @patch('api.Purchases.models.PurchaseDetail.objects.filter')
    def test_get_details_by_purchase_exception(self, mock_filter):
        """Test: excepcion en get_details_by_purchase"""
        mock_filter.side_effect = Exception('Database error')
        url = reverse('purchase-detail-get-details-by-purchase', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA search_details ====================

    @patch('api.Purchases.views.PurchaseDetailViewSet.filter_queryset')
    @patch('api.Purchases.views.PurchaseDetailViewSet.get_queryset')
    @patch('api.Purchases.views.PurchaseDetailViewSet.get_serializer')
    def test_search_details_success(self, mock_get_serializer, mock_get_queryset, mock_filter_queryset):
        """Test: buscar detalles con resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'variant__sku': 'SKU001'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_search_details, {'search': 'SKU001'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'resultados obtenidos')

    @patch('api.Purchases.views.PurchaseDetailViewSet.filter_queryset')
    @patch('api.Purchases.views.PurchaseDetailViewSet.get_queryset')
    def test_search_details_empty(self, mock_get_queryset, mock_filter_queryset):
        """Test: buscar detalles sin resultados"""
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = False
        mock_filter_queryset.return_value = mock_filtered
        response = self.client.get(self.url_search_details, {'search': 'XYZ999'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['results'], [])

    @patch('api.Purchases.views.PurchaseDetailViewSet.get_queryset')
    def test_search_details_exception(self, mock_get_queryset):
        """Test: excepcion en search_details"""
        mock_get_queryset.side_effect = Exception('Search error')
        response = self.client.get(self.url_search_details)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


# =============================================================================
# TESTS PARA IvaViewSets
# =============================================================================

class IvaViewSetsTestCase(APITestCase):
    """Test cases para IvaViewSets (ModelViewSet)"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = IvaViewSets()
        self.assertEqual(viewset.queryset.model, Iva)
        self.assertEqual(viewset.serializer_class, IvaSerializer)
        self.assertEqual(viewset.required_module, 'Compras')

    def test_list_iva(self):
        """Test: listar IVA (ModelViewSet list)"""
        with patch('api.Purchases.views.IvaViewSets.get_queryset') as mock_qs, \
             patch('api.Purchases.views.IvaViewSets.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_serializer = MagicMock()
            mock_serializer.data = [{'id': 1, 'percentage': 19.0}]
            mock_ser.return_value = mock_serializer
            response = self.client.get(reverse('iva-list'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_retrieve_iva(self):
        """Test: obtener IVA por ID (ModelViewSet retrieve)"""
        with patch('api.Purchases.views.IvaViewSets.get_object') as mock_obj, \
             patch('api.Purchases.views.IvaViewSets.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock(id=1)
            mock_serializer = MagicMock()
            mock_serializer.data = {'id': 1, 'percentage': 19.0}
            mock_ser.return_value = mock_serializer
            response = self.client.get(reverse('iva-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_create_iva(self):
        """Test: crear IVA (ModelViewSet create)"""
        with patch('api.Purchases.views.IvaViewSets.get_serializer') as mock_ser:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1, 'percentage': 19.0}
            mock_ser.return_value = mock_serializer
            response = self.client.post(reverse('iva-list'), {'percentage': 19.0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_update_iva(self):
        """Test: actualizar IVA (ModelViewSet update)"""
        with patch('api.Purchases.views.IvaViewSets.get_object') as mock_obj, \
             patch('api.Purchases.views.IvaViewSets.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock(id=1)
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1, 'percentage': 21.0}
            mock_ser.return_value = mock_serializer
            response = self.client.put(reverse('iva-detail', kwargs={'pk': 1}), {'percentage': 21.0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_delete_iva(self):
        """Test: eliminar IVA (ModelViewSet destroy)"""
        with patch('api.Purchases.views.IvaViewSets.get_object') as mock_obj:
            mock_iva = MagicMock()
            mock_iva.delete = MagicMock()
            mock_obj.return_value = mock_iva
            response = self.client.delete(reverse('iva-detail', kwargs={'pk': 1}))
        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)

# Create your tests here.
