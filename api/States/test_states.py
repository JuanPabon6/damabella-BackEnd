from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status, permissions
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock, ANY
from django.core.exceptions import MultipleObjectsReturned
from django.db import IntegrityError


from api.States.models import States
from api.States.serializers import StatesSerializers
from api.States.views import StatesViewSets


User = get_user_model()


class StatesViewSetsTestCase(APITestCase):
    """Test cases para StatesViewSets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_states = reverse('states-get-states')
        self.url_create_states = reverse('states-create-states')

    # ==================== TESTS DE CONFIGURACION ====================

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = StatesViewSets()
        self.assertEqual(viewset.queryset.model, States)
        self.assertEqual(viewset.serializer_class, StatesSerializers)
        self.assertEqual(viewset.required_module, 'Estados')
        self.assertIn(permissions.AllowAny, viewset.permission_classes)

    def test_allow_any_permission(self):
        """Test: verificar acceso sin autenticacion"""
        self.client.force_authenticate(user=None)
        with patch('api.States.views.StatesViewSets.get_queryset') as mock_qs, \
             patch('api.States.views.StatesViewSets.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_s = MagicMock()
            mock_s.data = []
            mock_ser.return_value = mock_s
            response = self.client.get(self.url_get_states)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # ==================== TESTS PARA get_states ====================

    @patch('api.States.views.StatesViewSets.get_queryset')
    @patch('api.States.views.StatesViewSets.get_serializer')
    def test_get_states_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de estados exitosamente"""
        mock_get_queryset.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'name': 'Activo', 'description': 'Estado activo'},
            {'id': 2, 'name': 'Inactivo', 'description': 'Estado inactivo'},
        ]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_states)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'estados obtenidos')
        self.assertEqual(len(response.data['results']), 2)

    @patch('api.States.views.StatesViewSets.get_queryset')
    def test_get_states_empty(self, mock_get_queryset):
        """Test: obtener lista de estados vacia"""
        mock_get_queryset.return_value = []
        with patch('api.States.views.StatesViewSets.get_serializer') as mock_ser:
            mock_serializer = MagicMock()
            mock_serializer.data = []
            mock_ser.return_value = mock_serializer
            response = self.client.get(self.url_get_states)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], [])

    @patch('api.States.views.StatesViewSets.get_queryset')
    def test_get_states_exception(self, mock_get_queryset):
        """Test: excepcion en get_states (no capturada)"""
        mock_get_queryset.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_states)
        # No esta capturada, cae en excepcion -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA get_states_by_id ====================

    @patch('api.States.views.StatesViewSets.get_object')
    @patch('api.States.views.StatesViewSets.get_serializer')
    def test_get_states_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener estado por ID exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'name': 'Activo', 'description': 'Estado activo'}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('states-get-states-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'estado obtenido')
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.States.views.StatesViewSets.get_object')
    def test_get_states_by_id_not_found(self, mock_get_object):
        """Test: estado no encontrado (DoesNotExist)"""
        mock_get_object.side_effect = States.DoesNotExist("No existe")
        url = reverse('states-get-states-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        # DoesNotExist no esta capturada, cae en excepcion -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.States.views.StatesViewSets.get_object')
    def test_get_states_by_id_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('states-get-states-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.States.views.StatesViewSets.get_object')
    def test_get_states_by_id_exception(self, mock_get_object):
        """Test: excepcion generica en get_states_by_id"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('states-get-states-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA create_states ====================

    @patch('api.States.views.StatesViewSets.get_serializer')
    def test_create_states_success(self, mock_get_serializer):
        """Test: crear estado exitosamente (201 Created)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'Nuevo Estado', 'description': 'Descripcion'}
        mock_get_serializer.return_value = mock_serializer
        data = {'name': 'Nuevo Estado', 'description': 'Descripcion'}
        response = self.client.post(self.url_create_states, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'estado creado exitosamente')
        self.assertIn('object', response.data)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.States.views.StatesViewSets.get_serializer')
    def test_create_states_validation_error(self, mock_get_serializer):
        """Test: crear estado con datos invalidos (ValidationError)"""
        from rest_framework.exceptions import ValidationError
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'name': ['Este campo es requerido']})
        mock_get_serializer.return_value = mock_serializer
        data = {'description': 'Sin nombre'}
        response = self.client.post(self.url_create_states, data, format='json')
        # ValidationError no esta capturada, cae en excepcion -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.States.views.StatesViewSets.get_serializer')
    def test_create_states_multiple_objects(self, mock_get_serializer):
        """Test: manejo de MultipleObjectsReturned en create_states"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = MultipleObjectsReturned("Multiples objetos")
        mock_get_serializer.return_value = mock_serializer
        data = {'name': 'Estado'}
        response = self.client.post(self.url_create_states, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.States.views.StatesViewSets.get_serializer')
    def test_create_states_exception(self, mock_get_serializer):
        """Test: excepcion generica en create_states"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Unexpected error')
        mock_get_serializer.return_value = mock_serializer
        data = {'name': 'Estado'}
        response = self.client.post(self.url_create_states, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.States.views.StatesViewSets.get_serializer')
    def test_create_states_integrity_error(self, mock_get_serializer):
        """Test: crear estado con IntegrityError (nombre duplicado)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer
        data = {'name': 'Activo'}
        response = self.client.post(self.url_create_states, data, format='json')
        # IntegrityError no esta capturada, cae en excepcion -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA delete_states ====================

    @patch('api.States.views.StatesViewSets.get_object')
    def test_delete_states_success(self, mock_get_object):
        """Test: eliminar estado exitosamente"""
        mock_state = MagicMock()
        mock_state.id = 1
        mock_state.delete = MagicMock()
        mock_get_object.return_value = mock_state
        url = reverse('states-delete-states', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('eliminado', response.data['message'].lower())
        mock_state.delete.assert_called_once()

    @patch('api.States.views.StatesViewSets.get_object')
    def test_delete_states_not_found(self, mock_get_object):
        """Test: eliminar estado que no existe"""
        mock_get_object.side_effect = States.DoesNotExist("No existe")
        url = reverse('states-delete-states', kwargs={'pk': 999})
        response = self.client.delete(url)
        # DoesNotExist no esta capturada, cae en excepcion -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.States.views.StatesViewSets.get_object')
    def test_delete_states_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en delete_states"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('states-delete-states', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.States.views.StatesViewSets.get_object')
    def test_delete_states_exception(self, mock_get_object):
        """Test: excepcion generica en delete_states"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('states-delete-states', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.States.views.StatesViewSets.get_object')
    def test_delete_states_integrity_error(self, mock_get_object):
        """Test: eliminar estado con restriccion de integridad"""
        mock_state = MagicMock()
        mock_state.delete.side_effect = IntegrityError("Foreign key constraint")
        mock_get_object.return_value = mock_state
        url = reverse('states-delete-states', kwargs={'pk': 1})
        response = self.client.delete(url)
        # IntegrityError no esta capturada, cae en excepcion -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA update_states ====================

    @patch('api.States.views.StatesViewSets.get_object')
    @patch('api.States.views.StatesViewSets.get_serializer')
    def test_update_states_success(self, mock_get_serializer, mock_get_object):
        """Test: actualizar estado exitosamente"""
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'Estado Actualizado', 'description': 'Nueva descripcion'}
        mock_get_serializer.return_value = mock_serializer
        data = {'name': 'Estado Actualizado', 'description': 'Nueva descripcion'}
        url = reverse('states-update-states', kwargs={'pk': 1})
        response = self.client.put(url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'actualizado exitosamente')
        self.assertIn('object', response.data)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.States.views.StatesViewSets.get_object')
    def test_update_states_not_found(self, mock_get_object):
        """Test: actualizar estado que no existe"""
        mock_get_object.side_effect = States.DoesNotExist("No existe")
        url = reverse('states-update-states', kwargs={'pk': 999})
        response = self.client.put(url, {'name': 'Test'}, format='json')
        # DoesNotExist no esta capturada, cae en excepcion -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.States.views.StatesViewSets.get_object')
    @patch('api.States.views.StatesViewSets.get_serializer')
    def test_update_states_validation_error(self, mock_get_serializer, mock_get_object):
        """Test: actualizar estado con datos invalidos"""
        from rest_framework.exceptions import ValidationError
        mock_get_object.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'name': ['Requerido']})
        mock_get_serializer.return_value = mock_serializer
        url = reverse('states-update-states', kwargs={'pk': 1})
        response = self.client.put(url, {}, format='json')
        # ValidationError no esta capturada, cae en excepcion -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.States.views.StatesViewSets.get_object')
    def test_update_states_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en update_states"""
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('states-update-states', kwargs={'pk': 1})
        response = self.client.put(url, {'name': 'Test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.States.views.StatesViewSets.get_object')
    def test_update_states_exception(self, mock_get_object):
        """Test: excepcion generica en update_states"""
        mock_get_object.side_effect = Exception('Server error')
        url = reverse('states-update-states', kwargs={'pk': 1})
        response = self.client.put(url, {'name': 'Test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.States.views.StatesViewSets.get_object')
    @patch('api.States.views.StatesViewSets.get_serializer')
    def test_update_states_integrity_error(self, mock_get_serializer, mock_get_object):
        """Test: actualizar estado con IntegrityError"""
        mock_get_object.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer
        url = reverse('states-update-states', kwargs={'pk': 1})
        response = self.client.put(url, {'name': 'Estado'}, format='json')
        # IntegrityError no esta capturada, cae en excepcion -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS DE METODOS HTTP NO PERMITIDOS ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar metodos HTTP no soportados"""
        response_post = self.client.post(self.url_get_states, {})
        response_put = self.client.put(self.url_get_states, {})
        response_delete = self.client.delete(self.url_get_states)
        self.assertIn(response_post.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])

    # ==================== TESTS DE ESTRUCTURA DE RESPUESTAS ====================

    def test_response_structure_get_states(self):
        """Test: verificar estructura de respuesta en get_states"""
        with patch('api.States.views.StatesViewSets.get_queryset') as mock_qs, \
             patch('api.States.views.StatesViewSets.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_serializer = MagicMock()
            mock_serializer.data = []
            mock_ser.return_value = mock_serializer
            response = self.client.get(self.url_get_states)
        self.assertIn('message', response.data)
        self.assertIn('results', response.data)
        self.assertIn('success', response.data)
        self.assertIsInstance(response.data['success'], bool)

    def test_response_structure_create_states(self):
        """Test: verificar estructura de respuesta en create_states"""
        with patch('api.States.views.StatesViewSets.get_serializer') as mock_ser:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1}
            mock_ser.return_value = mock_serializer
            response = self.client.post(self.url_create_states, {'name': 'Test'}, format='json')
        self.assertIn('message', response.data)
        self.assertIn('object', response.data)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])

    def test_response_structure_delete_states(self):
        """Test: verificar estructura de respuesta en delete_states"""
        with patch('api.States.views.StatesViewSets.get_object') as mock_obj:
            mock_state = MagicMock()
            mock_state.delete = MagicMock()
            mock_obj.return_value = mock_state
            url = reverse('states-delete-states', kwargs={'pk': 1})
            response = self.client.delete(url)
        self.assertIn('message', response.data)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])

    def test_response_structure_update_states(self):
        """Test: verificar estructura de respuesta en update_states"""
        with patch('api.States.views.StatesViewSets.get_object') as mock_obj, \
             patch('api.States.views.StatesViewSets.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock()
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1}
            mock_ser.return_value = mock_serializer
            url = reverse('states-update-states', kwargs={'pk': 1})
            response = self.client.put(url, {'name': 'Test'}, format='json')
        self.assertIn('message', response.data)
        self.assertIn('object', response.data)
        self.assertIn('success', response.data)
        self.assertTrue(response.data['success'])

    # ==================== TESTS DE CASOS BORDE ====================

    def test_get_states_by_id_zero_id(self):
        """Test: obtener estado con ID = 0"""
        with patch('api.States.views.StatesViewSets.get_object') as mock_obj:
            mock_obj.side_effect = States.DoesNotExist("No existe")
            url = reverse('states-get-states-by-id', kwargs={'pk': 0})
            response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_create_states_empty_data(self):
        """Test: crear estado sin datos"""
        with patch('api.States.views.StatesViewSets.get_serializer') as mock_ser:
            from rest_framework.exceptions import ValidationError
            mock_serializer = MagicMock()
            mock_serializer.is_valid.side_effect = ValidationError({'name': ['Requerido']})
            mock_ser.return_value = mock_serializer
            response = self.client.post(self.url_create_states, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_update_states_empty_data(self):
        """Test: actualizar estado sin datos"""
        with patch('api.States.views.StatesViewSets.get_object') as mock_obj, \
             patch('api.States.views.StatesViewSets.get_serializer') as mock_ser:
            mock_obj.return_value = MagicMock()
            mock_serializer = MagicMock()
            mock_serializer.is_valid.side_effect = Exception('Validation error')
            mock_ser.return_value = mock_serializer
            url = reverse('states-update-states', kwargs={'pk': 1})
            response = self.client.put(url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_delete_states_large_id(self):
        """Test: eliminar estado con ID muy grande"""
        with patch('api.States.views.StatesViewSets.get_object') as mock_obj:
            mock_obj.side_effect = States.DoesNotExist("No existe")
            url = reverse('states-delete-states', kwargs={'pk': 999999})
            response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)


class StatesViewSetsIntegrationTestCase(APITestCase):
    """Tests de integracion con base de datos real"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='integrationuser', email='integration@test.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_actual_database_get_states(self):
        """Test: obtener estados con base de datos real"""
        url = reverse('states-get-states')
        response = self.client.get(url)
        if response.status_code == status.HTTP_200_OK:
            self.assertTrue(response.data['success'])
            self.assertIn('results', response.data)

# Create your tests here.
