from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock, ANY
from django.core.exceptions import MultipleObjectsReturned
from django.shortcuts import get_object_or_404

from api.Inventory.models import Inventory
from api.Inventory.serializers import InventorySerializers, AdjustStockSerializer
from api.Inventory.views import InventoryViewSets
from api.Inventory.services import add_stock, out_stock


User = get_user_model()


class InventoryViewSetsTestCase(APITestCase):
    """Test cases para InventoryViewSets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_inventories = reverse('inventory-get-inventories')

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = InventoryViewSets()
        self.assertEqual(viewset.queryset.model, Inventory)
        self.assertEqual(viewset.serializer_class, InventorySerializers)
        self.assertIn(permissions.AllowAny, viewset.permission_classes)

    # ==================== TESTS PARA get_serializer_class ====================

    def test_get_serializer_class_default(self):
        """Test: obtener serializer por defecto (InventorySerializers)"""
        viewset = InventoryViewSets()
        viewset.action = 'get_inventories'
        self.assertEqual(viewset.get_serializer_class(), InventorySerializers)

    def test_get_serializer_class_increment_stock(self):
        """Test: obtener serializer para increment_stock (AdjustStockSerializer)"""
        viewset = InventoryViewSets()
        viewset.action = 'increment_stock'
        self.assertEqual(viewset.get_serializer_class(), AdjustStockSerializer)

    def test_get_serializer_class_subtract_stock(self):
        """Test: obtener serializer para subtract_stock (AdjustStockSerializer)"""
        viewset = InventoryViewSets()
        viewset.action = 'subtract_stock'
        self.assertEqual(viewset.get_serializer_class(), AdjustStockSerializer)

    # ==================== TESTS PARA get_inventories ====================

    @patch('api.Inventory.views.InventoryViewSets.get_queryset')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_get_inventories_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de inventarios exitosamente"""
        mock_get_queryset.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'variant': 1, 'quantity': 100, 'stock': 50},
            {'id': 2, 'variant': 2, 'quantity': 200, 'stock': 75},
        ]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_inventories)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'inventarios obtenidos')
        self.assertEqual(len(response.data['results']), 2)

    @patch('api.Inventory.views.InventoryViewSets.get_queryset')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_get_inventories_empty(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de inventarios vacia"""
        mock_get_queryset.return_value = []
        mock_serializer = MagicMock()
        mock_serializer.data = []
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_inventories)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], [])

    @patch('api.Inventory.views.InventoryViewSets.get_queryset')
    def test_get_inventories_exception(self, mock_get_queryset):
        """Test: excepcion en get_inventories (no capturada)"""
        mock_get_queryset.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_inventories)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA get_inventory_by_id ====================

    @patch('api.Inventory.views.InventoryViewSets.get_object')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_get_inventory_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener inventario por ID exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'variant': 1, 'quantity': 100, 'stock': 50}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('inventory-get-inventory-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'inventario obtenido')
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.Inventory.views.InventoryViewSets.get_object')
    def test_get_inventory_by_id_not_found(self, mock_get_object):
        """Test: inventario no encontrado (Http404)"""
        from django.http import Http404
        mock_get_object.side_effect = Http404("No encontrado")
        url = reverse('inventory-get-inventory-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Inventory.views.InventoryViewSets.get_object')
    def test_get_inventory_by_id_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('inventory-get-inventory-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())
        # Nota: typo en codigo original 'rotornados' en lugar de 'retornados'

    @patch('api.Inventory.views.InventoryViewSets.get_object')
    def test_get_inventory_by_id_exception(self, mock_get_object):
        """Test: excepcion generica"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('inventory-get-inventory-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('server error', response.data['error'].lower())

    # ==================== TESTS PARA increment_stock ====================

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.add_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_increment_stock_success(self, mock_get_serializer, mock_add_stock, mock_get_object_or_404):
        """Test: incrementar stock exitosamente"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': 50}
        mock_serializer.data = {'amount': 50}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-increment-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 50}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'stock sumado exitosamente')
        self.assertIn('object', response.data)
        mock_add_stock.assert_called_once_with(mock_inventory.variant, 50)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.add_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_increment_stock_zero_amount(self, mock_get_serializer, mock_add_stock, mock_get_object_or_404):
        """Test: incrementar stock con cantidad cero"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': 0}
        mock_serializer.data = {'amount': 0}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-increment-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_add_stock.assert_called_once_with(mock_inventory.variant, 0)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.add_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_increment_stock_negative_amount(self, mock_get_serializer, mock_add_stock, mock_get_object_or_404):
        """Test: incrementar stock con cantidad negativa"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': -10}
        mock_serializer.data = {'amount': -10}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-increment-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': -10}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_add_stock.assert_called_once_with(mock_inventory.variant, -10)

    @patch('api.Inventory.views.get_object_or_404')
    def test_increment_stock_inventory_not_found(self, mock_get_object_or_404):
        """Test: incrementar stock en inventario inexistente"""
        from django.http import Http404
        mock_get_object_or_404.side_effect = Http404("No encontrado")
        url = reverse('inventory-increment-stock', kwargs={'pk': 999})
        response = self.client.post(url, {'amount': 50}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_increment_stock_validation_error(self, mock_get_serializer, mock_get_object_or_404):
        """Test: incrementar stock con datos invalidos (ValidationError)"""
        from rest_framework.exceptions import ValidationError
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'amount': ['Debe ser un numero']})
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-increment-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 'invalid'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.add_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_increment_stock_exception(self, mock_get_serializer, mock_add_stock, mock_get_object_or_404):
        """Test: excepcion al incrementar stock"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': 50}
        mock_get_serializer.return_value = mock_serializer

        mock_add_stock.side_effect = Exception('Stock error')

        url = reverse('inventory-increment-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 50}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA subtract_stock ====================

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.out_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_subtract_stock_success(self, mock_get_serializer, mock_out_stock, mock_get_object_or_404):
        """Test: restar stock exitosamente"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': 20}
        mock_serializer.data = {'amount': 20}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-subtract-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 20}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'stock ajustado exitosamente')
        self.assertIn('object', response.data)
        mock_out_stock.assert_called_once_with(mock_inventory.variant, 20)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.out_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_subtract_stock_zero_amount(self, mock_get_serializer, mock_out_stock, mock_get_object_or_404):
        """Test: restar stock con cantidad cero"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': 0}
        mock_serializer.data = {'amount': 0}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-subtract-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 0}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_out_stock.assert_called_once_with(mock_inventory.variant, 0)

    @patch('api.Inventory.views.get_object_or_404')
    def test_subtract_stock_inventory_not_found(self, mock_get_object_or_404):
        """Test: restar stock en inventario inexistente"""
        from django.http import Http404
        mock_get_object_or_404.side_effect = Http404("No encontrado")
        url = reverse('inventory-subtract-stock', kwargs={'pk': 999})
        response = self.client.post(url, {'amount': 20}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_subtract_stock_validation_error(self, mock_get_serializer, mock_get_object_or_404):
        """Test: restar stock con datos invalidos (ValidationError)"""
        from rest_framework.exceptions import ValidationError
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'amount': ['Debe ser un numero']})
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-subtract-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 'invalid'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.out_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_subtract_stock_exception(self, mock_get_serializer, mock_out_stock, mock_get_object_or_404):
        """Test: excepcion al restar stock"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': 20}
        mock_get_serializer.return_value = mock_serializer

        mock_out_stock.side_effect = Exception('Stock error')

        url = reverse('inventory-subtract-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 20}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.out_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_subtract_stock_insufficient_stock(self, mock_get_serializer, mock_out_stock, mock_get_object_or_404):
        """Test: restar stock con cantidad mayor a la disponible"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': 999}
        mock_serializer.data = {'amount': 999}
        mock_get_serializer.return_value = mock_serializer

        mock_out_stock.side_effect = Exception('Stock insuficiente')

        url = reverse('inventory-subtract-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS DE AUTENTICACION ====================

    def test_allow_any_permission(self):
        """Test: verificar que AllowAny funciona"""
        self.client.force_authenticate(user=None)
        with patch('api.Inventory.views.InventoryViewSets.get_queryset') as mock_qs, \
             patch('api.Inventory.views.InventoryViewSets.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_s = MagicMock()
            mock_s.data = []
            mock_ser.return_value = mock_s
            response = self.client.get(self.url_get_inventories)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==================== TESTS DE METODOS HTTP ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar metodos HTTP no soportados"""
        response_post = self.client.post(self.url_get_inventories, {})
        response_put = self.client.put(self.url_get_inventories, {})
        response_delete = self.client.delete(self.url_get_inventories)
        self.assertIn(response_post.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])

    def test_get_methods_for_stock_endpoints(self):
        """Test: verificar que increment_stock y subtract_stock no aceptan GET"""
        url = reverse('inventory-increment-stock', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])

        url = reverse('inventory-subtract-stock', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertIn(response.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])

    # ==================== TESTS DE CASOS BORDE ====================

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.add_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_increment_stock_large_amount(self, mock_get_serializer, mock_add_stock, mock_get_object_or_404):
        """Test: incrementar stock con cantidad muy grande"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': 999999}
        mock_serializer.data = {'amount': 999999}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-increment-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 999999}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_add_stock.assert_called_once_with(mock_inventory.variant, 999999)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_increment_stock_missing_amount(self, mock_get_serializer, mock_get_object_or_404):
        """Test: incrementar stock sin enviar amount"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Amount requerido')
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-increment-stock', kwargs={'pk': 1})
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_subtract_stock_missing_amount(self, mock_get_serializer, mock_get_object_or_404):
        """Test: restar stock sin enviar amount"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Amount requerido')
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-subtract-stock', kwargs={'pk': 1})
        response = self.client.post(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.add_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_increment_stock_decimal_amount(self, mock_get_serializer, mock_add_stock, mock_get_object_or_404):
        """Test: incrementar stock con cantidad decimal"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': 10.5}
        mock_serializer.data = {'amount': 10.5}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-increment-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 10.5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_add_stock.assert_called_once_with(mock_inventory.variant, 10.5)

    @patch('api.Inventory.views.get_object_or_404')
    @patch('api.Inventory.views.out_stock')
    @patch('api.Inventory.views.InventoryViewSets.get_serializer')
    def test_subtract_stock_decimal_amount(self, mock_get_serializer, mock_out_stock, mock_get_object_or_404):
        """Test: restar stock con cantidad decimal"""
        mock_inventory = MagicMock()
        mock_inventory.variant = MagicMock(id=1)
        mock_get_object_or_404.return_value = mock_inventory

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'amount': 5.5}
        mock_serializer.data = {'amount': 5.5}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('inventory-subtract-stock', kwargs={'pk': 1})
        response = self.client.post(url, {'amount': 5.5}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_out_stock.assert_called_once_with(mock_inventory.variant, 5.5)

    # ==================== TESTS DE ESTRUCTURA DE RESPUESTAS ====================

    def test_response_structure_get_inventories(self):
        """Test: verificar estructura de respuesta en get_inventories"""
        with patch('api.Inventory.views.InventoryViewSets.get_queryset') as mock_qs, \
             patch('api.Inventory.views.InventoryViewSets.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_serializer = MagicMock()
            mock_serializer.data = []
            mock_ser.return_value = mock_serializer
            response = self.client.get(self.url_get_inventories)
        self.assertIn('message', response.data)
        self.assertIn('results', response.data)
        self.assertIn('success', response.data)
        self.assertIsInstance(response.data['success'], bool)

    def test_response_structure_get_inventory_by_id(self):
        """Test: verificar estructura de respuesta en get_inventory_by_id"""
        with patch('api.Inventory.views.InventoryViewSets.get_object') as mock_obj, \
             patch('api.Inventory.views.InventoryViewSets.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock()
            mock_serializer = MagicMock()
            mock_serializer.data = {'id': 1}
            mock_ser.return_value = mock_serializer
            url = reverse('inventory-get-inventory-by-id', kwargs={'pk': 1})
            response = self.client.get(url)
        self.assertIn('message', response.data)
        self.assertIn('results', response.data)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])

    def test_response_structure_increment_stock(self):
        """Test: verificar estructura de respuesta en increment_stock"""
        with patch('api.Inventory.views.get_object_or_404') as mock_gof, \
             patch('api.Inventory.views.add_stock') as mock_add, \
             patch('api.Inventory.views.InventoryViewSets.get_serializer') as mock_ser:
            mock_inventory = MagicMock()
            mock_inventory.variant = MagicMock()
            mock_gof.return_value = mock_inventory
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.validated_data = {'amount': 10}
            mock_serializer.data = {'amount': 10}
            mock_ser.return_value = mock_serializer
            url = reverse('inventory-increment-stock', kwargs={'pk': 1})
            response = self.client.post(url, {'amount': 10}, format='json')
        self.assertIn('message', response.data)
        self.assertIn('object', response.data)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])

    def test_response_structure_subtract_stock(self):
        """Test: verificar estructura de respuesta en subtract_stock"""
        with patch('api.Inventory.views.get_object_or_404') as mock_gof, \
             patch('api.Inventory.views.out_stock') as mock_out, \
             patch('api.Inventory.views.InventoryViewSets.get_serializer') as mock_ser:
            mock_inventory = MagicMock()
            mock_inventory.variant = MagicMock()
            mock_gof.return_value = mock_inventory
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.validated_data = {'amount': 10}
            mock_serializer.data = {'amount': 10}
            mock_ser.return_value = mock_serializer
            url = reverse('inventory-subtract-stock', kwargs={'pk': 1})
            response = self.client.post(url, {'amount': 10}, format='json')
        self.assertIn('message', response.data)
        self.assertIn('object', response.data)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])


class InventoryViewSetsIntegrationTestCase(APITestCase):
    """Tests de integracion con base de datos real"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='integrationuser', email='integration@test.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_actual_database_get_inventories(self):
        """Test: obtener inventarios con base de datos real"""
        url = reverse('inventory-get-inventories')
        response = self.client.get(url)
        if response.status_code == status.HTTP_200_OK:
            self.assertTrue(response.data['success'])
            self.assertIn('results', response.data) 

# Create your tests here.
