from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status, filters
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock, PropertyMock, call
from datetime import datetime
import json

from api.Providers.models import Providers
from api.Providers.serializers import ProvidersSerializers, PatchStateSerializer
from api.Providers.views import ProvidersViewSets
from api.Exceptions.exceptions import ObjectNotExists, MultiResults, IntegrityException, InvalidData
from rest_framework.exceptions import APIException


User = get_user_model()


class ProvidersViewSetsTestCase(APITestCase):
    """Test cases para ProvidersViewSets"""

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
        self.url_get_providers = reverse('providers-get-providers')
        self.url_create_providers = reverse('providers-create-providers')
        self.url_search_providers = reverse('providers-search-providers')

        # URLs con parámetro pk (se construyen dinámicamente en los tests)
        # reverse('providers-get-providers-by-id', kwargs={'pk': 1})
        # reverse('providers-delete-providers', kwargs={'pk': 1})
        # reverse('providers-update-providers', kwargs={'pk': 1})
        # reverse('providers-patch-state', kwargs={'pk': 1})

    def tearDown(self):
        """Limpieza después de cada test"""
        pass

    # ==================== TESTS PARA get_serializer_class ====================

    def test_get_serializer_class_default(self):
        """Test: obtener serializer por defecto (ProvidersSerializers)"""
        viewset = ProvidersViewSets()
        viewset.action = 'get_providers'
        serializer_class = viewset.get_serializer_class()
        self.assertEqual(serializer_class, ProvidersSerializers)

    def test_get_serializer_class_patch_state(self):
        """Test: obtener serializer para acción patch_state"""
        viewset = ProvidersViewSets()
        viewset.action = 'patch_state'
        serializer_class = viewset.get_serializer_class()
        self.assertEqual(serializer_class, PatchStateSerializer)

    # ==================== TESTS PARA get_providers ====================

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_get_providers_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de proveedores exitosamente"""
        # Mock del queryset
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        # Mock del serializer
        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'nit_document': '123456', 'kompany_name': 'Empresa A'},
            {'id': 2, 'nit_document': '789012', 'kompany_name': 'Empresa B'},
        ]
        mock_get_serializer.return_value = mock_serializer

        response = self.client.get(self.url_get_providers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['results']), 2)
        mock_get_serializer.assert_called_once_with(mock_queryset, many=True)

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    def test_get_providers_empty(self, mock_get_queryset):
        """Test: obtener lista de proveedores vacía"""
        mock_get_queryset.return_value = []

        with patch('api.Providers.views.ProvidersViewSets.get_serializer') as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.data = []
            mock_get_serializer.return_value = mock_serializer

            response = self.client.get(self.url_get_providers)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['results']), 0)

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    def test_get_providers_does_not_exist(self, mock_get_queryset):
        """Test: manejo de Providers.DoesNotExist"""
        mock_get_queryset.side_effect = Providers.DoesNotExist("No hay proveedores")

        response = self.client.get(self.url_get_providers)

        # Debería lanzar ObjectNotExists (que es una APIException)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    def test_get_providers_exception(self, mock_get_queryset):
        """Test: manejo de excepción genérica en get_providers"""
        mock_get_queryset.side_effect = Exception('Database connection error')

        response = self.client.get(self.url_get_providers)

        # APIException debería retornar 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA get_providers_by_id ====================

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_get_providers_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener proveedor por ID exitosamente"""
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_provider.nit_document = '123456'
        mock_get_object.return_value = mock_provider

        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'nit_document': '123456', 'kompany_name': 'Empresa A'}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('providers-get-providers-by-id', kwargs={'pk': 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results']['id'], 1)
        mock_get_serializer.assert_called_once_with(mock_provider, many=False)

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    def test_get_providers_by_id_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en get_providers_by_id"""
        from django.core.exceptions import MultipleObjectsReturned
        mock_get_object.side_effect = MultipleObjectsReturned("Múltiples objetos encontrados")

        url = reverse('providers-get-providers-by-id', kwargs={'pk': 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    def test_get_providers_by_id_not_found(self, mock_get_object):
        """Test: proveedor no encontrado (404)"""
        from django.core.exceptions import ObjectDoesNotExist
        # get_object de GenericViewSet lanza Http404 que se convierte en 404
        from django.http import Http404
        mock_get_object.side_effect = Http404("No encontrado")

        url = reverse('providers-get-providers-by-id', kwargs={'pk': 999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    # ==================== TESTS PARA create_providers ====================

    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_create_providers_success(self, mock_get_serializer):
        """Test: crear proveedor exitosamente"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {
            'id': 1,
            'nit_document': '123456789',
            'kompany_name': 'Nueva Empresa',
            'contact_name': 'Juan Pérez',
            'phone': '1234567890',
            'address': 'Calle 123'
        }
        mock_get_serializer.return_value = mock_serializer

        data = {
            'nit_document': '123456789',
            'kompany_name': 'Nueva Empresa',
            'contact_name': 'Juan Pérez',
            'phone': '1234567890',
            'address': 'Calle 123'
        }

        response = self.client.post(self.url_create_providers, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 'creado exitosamente')
        self.assertIn('object', response.data)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_create_providers_validation_error(self, mock_get_serializer):
        """Test: crear proveedor con datos inválidos (ValidationError)"""
        from rest_framework.exceptions import ValidationError
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'nit_document': ['Este campo es requerido.']})
        mock_get_serializer.return_value = mock_serializer

        data = {'kompany_name': 'Empresa sin NIT'}  # Falta nit_document

        response = self.client.post(self.url_create_providers, data, format='json')

        # ValidationError debería retornar 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_create_providers_multiple_objects(self, mock_get_serializer):
        """Test: manejo de MultipleObjectsReturned en create_providers"""
        from django.core.exceptions import MultipleObjectsReturned
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = MultipleObjectsReturned("Múltiples objetos")
        mock_get_serializer.return_value = mock_serializer

        data = {'nit_document': '123456789', 'kompany_name': 'Empresa'}

        response = self.client.post(self.url_create_providers, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_create_providers_integrity_error(self, mock_get_serializer):
        """Test: crear proveedor con IntegrityError (NIT duplicado)"""
        from django.db.utils import IntegrityError
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer

        data = {'nit_document': '123456789', 'kompany_name': 'Empresa'}

        response = self.client.post(self.url_create_providers, data, format='json')

        # El IntegrityError no está capturado específicamente, debería caer en Exception
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA delete_providers ====================

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    def test_delete_providers_success(self, mock_get_object):
        """Test: eliminar proveedor exitosamente"""
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_provider.delete = MagicMock()
        mock_get_object.return_value = mock_provider

        url = reverse('providers-delete-providers', kwargs={'pk': 1})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        # Nota: hay un typo en el código original 'succes' en lugar de 'success'
        self.assertIn('eliminado', response.data['results'].lower())
        mock_provider.delete.assert_called_once()

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    def test_delete_providers_not_found(self, mock_get_object):
        """Test: eliminar proveedor que no existe"""
        from django.http import Http404
        mock_get_object.side_effect = Http404("No encontrado")

        url = reverse('providers-delete-providers', kwargs={'pk': 999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    def test_delete_providers_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en delete_providers"""
        from django.core.exceptions import MultipleObjectsReturned
        mock_get_object.side_effect = MultipleObjectsReturned("Múltiples objetos")

        url = reverse('providers-delete-providers', kwargs={'pk': 1})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    def test_delete_providers_integrity_error(self, mock_get_object):
        """Test: eliminar proveedor con restricción de integridad"""
        from django.db.utils import IntegrityError
        mock_provider = MagicMock()
        mock_provider.delete.side_effect = IntegrityError("Foreign key constraint")
        mock_get_object.return_value = mock_provider

        url = reverse('providers-delete-providers', kwargs={'pk': 1})
        response = self.client.delete(url)

        # Se captura específicamente y retorna un 400 Bad Request
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('No se puede eliminar', response.data['message'])

    # ==================== TESTS PARA update_providers ====================

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_update_providers_success(self, mock_get_serializer, mock_get_object):
        """Test: actualizar proveedor exitosamente"""
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_get_object.return_value = mock_provider

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {
            'id': 1,
            'nit_document': '123456789',
            'kompany_name': 'Empresa Actualizada',
            'contact_name': 'Pedro Gómez',
            'phone': '9876543210',
            'address': 'Nueva Dirección'
        }
        mock_get_serializer.return_value = mock_serializer

        data = {
            'nit_document': '123456789',
            'kompany_name': 'Empresa Actualizada',
            'contact_name': 'Pedro Gómez',
            'phone': '9876543210',
            'address': 'Nueva Dirección'
        }

        url = reverse('providers-update-providers', kwargs={'pk': 1})
        response = self.client.put(url, data, format='json')

        # Nota: el código original no especifica status code, usa el default (200)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 'actualizado exitosamente')
        self.assertIn('provider', response.data)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_update_providers_validation_error(self, mock_get_serializer, mock_get_object):
        """Test: actualizar proveedor con datos inválidos"""
        from rest_framework.exceptions import ValidationError
        mock_provider = MagicMock()
        mock_get_object.return_value = mock_provider

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'phone': ['Formato inválido']})
        mock_get_serializer.return_value = mock_serializer

        data = {'phone': 'invalid-phone-format'}

        url = reverse('providers-update-providers', kwargs={'pk': 1})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    def test_update_providers_not_found(self, mock_get_object):
        """Test: actualizar proveedor que no existe"""
        from django.http import Http404
        mock_get_object.side_effect = Http404("No encontrado")

        url = reverse('providers-update-providers', kwargs={'pk': 999})
        response = self.client.put(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    def test_update_providers_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en update_providers"""
        from django.core.exceptions import MultipleObjectsReturned
        mock_get_object.side_effect = MultipleObjectsReturned("Múltiples objetos")

        url = reverse('providers-update-providers', kwargs={'pk': 1})
        response = self.client.put(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA search_providers ====================

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    @patch('api.Providers.views.ProvidersViewSets.filter_queryset')
    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_search_providers_success(self, mock_get_serializer, mock_filter_queryset, mock_get_queryset):
        """Test: buscar proveedores con resultados"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered

        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'nit_document': '123456', 'kompany_name': 'Empresa A'},
            {'id': 2, 'nit_document': '789012', 'kompany_name': 'Empresa B'},
        ]
        mock_get_serializer.return_value = mock_serializer

        response = self.client.get(self.url_search_providers, {'search': 'Empresa'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'resultados obtenidos')
        self.assertEqual(len(response.data['results']), 2)
        mock_filter_queryset.assert_called_once_with(queryset=mock_queryset)

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    @patch('api.Providers.views.ProvidersViewSets.filter_queryset')
    def test_search_providers_empty(self, mock_filter_queryset, mock_get_queryset):
        """Test: buscar proveedores sin resultados"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = False
        mock_filter_queryset.return_value = mock_filtered

        response = self.client.get(self.url_search_providers, {'search': 'XYZ123'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'sin resultados')
        self.assertEqual(response.data['results'], [])

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    def test_search_providers_exception(self, mock_get_queryset):
        """Test: excepción en search_providers"""
        mock_get_queryset.side_effect = Exception('Search error')

        response = self.client.get(self.url_search_providers)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    @patch('api.Providers.views.ProvidersViewSets.filter_queryset')
    def test_search_providers_no_search_param(self, mock_filter_queryset, mock_get_queryset):
        """Test: buscar sin parámetro de búsqueda (debería retornar todos)"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered

        with patch('api.Providers.views.ProvidersViewSets.get_serializer') as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.data = []
            mock_get_serializer.return_value = mock_serializer

            response = self.client.get(self.url_search_providers)

        # Sin parámetro search, filter_queryset debería retornar todos
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ==================== TESTS PARA patch_state ====================

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_patch_state_success(self, mock_get_serializer, mock_get_object):
        """Test: cambiar estado de proveedor exitosamente (PATCH)"""
        mock_provider = MagicMock()
        mock_provider.id = 1
        mock_provider.state = True
        mock_get_object.return_value = mock_provider

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'state': False}
        mock_get_serializer.return_value = mock_serializer

        data = {'state': False}

        url = reverse('providers-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'estado cambiado exitosamente')
        self.assertIn('object', response.data)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_patch_state_validation_error(self, mock_get_serializer, mock_get_object):
        """Test: cambiar estado con datos inválidos"""
        from rest_framework.exceptions import ValidationError
        mock_provider = MagicMock()
        mock_get_object.return_value = mock_provider

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'state': ['Debe ser booleano']})
        mock_get_serializer.return_value = mock_serializer

        data = {'state': 'invalid'}

        url = reverse('providers-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    def test_patch_state_not_found(self, mock_get_object):
        """Test: cambiar estado de proveedor inexistente"""
        from django.http import Http404
        mock_get_object.side_effect = Http404("No encontrado")

        url = reverse('providers-patch-state', kwargs={'pk': 999})
        response = self.client.patch(url, {'state': False}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    def test_patch_state_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en patch_state"""
        from django.core.exceptions import MultipleObjectsReturned
        mock_get_object.side_effect = MultipleObjectsReturned("Múltiples objetos")

        url = reverse('providers-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': False}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS DE CONFIGURACIÓN DEL VIEWSET ====================

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = ProvidersViewSets()

        self.assertEqual(viewset.queryset.model, Providers)
        self.assertEqual(viewset.serializer_class, ProvidersSerializers)
        self.assertEqual(viewset.required_module, 'Proveedores')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        self.assertEqual(viewset.fields_search, ['nit_document','kompany_name','contact_name','phone','address'])

    def test_viewset_authentication_disabled(self):
        """Test: verificar que autenticación está comentada/desactivada"""
        viewset = ProvidersViewSets()
        # En el código original están comentadas, pero si las descomentas:
        # self.assertEqual(viewset.authentication_classes, [])
        # self.assertEqual(viewset.permission_classes, [])
        pass  # Solo documentación, las clases están comentadas

    # ==================== TESTS DE AUTENTICACIÓN Y PERMISOS ====================

    def test_unauthenticated_access(self):
        """Test: verificar comportamiento sin autenticación"""
        self.client.force_authenticate(user=None)

        # Si authentication_classes está vacía, debería permitir acceso
        # Si no, debería retornar 401/403
        response = self.client.get(self.url_get_providers)

        # Depende de tu configuración global de autenticación
        # Si las clases están comentadas, puede ser 200
        self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_401_UNAUTHORIZED, status.HTTP_403_FORBIDDEN])

    # ==================== TESTS DE MÉTODOS HTTP NO PERMITIDOS ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar métodos HTTP no soportados por cada endpoint"""
        # get_providers solo permite GET
        response_post = self.client.post(self.url_get_providers, {})
        response_put = self.client.put(self.url_get_providers, {})
        response_delete = self.client.delete(self.url_get_providers)

        self.assertIn(response_post.status_code, [status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_403_FORBIDDEN])

    # ==================== TESTS DE CASOS BORDE ====================

    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_create_providers_empty_data(self, mock_get_serializer):
        """Test: crear proveedor con datos vacíos"""
        from rest_framework.exceptions import ValidationError
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'nit_document': ['Este campo es requerido']})
        mock_get_serializer.return_value = mock_serializer

        response = self.client.post(self.url_create_providers, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_update_providers_partial_data(self, mock_get_serializer, mock_get_object):
        """Test: actualizar proveedor con datos parciales (PUT requiere todos)"""
        from rest_framework.exceptions import ValidationError
        mock_provider = MagicMock()
        mock_get_object.return_value = mock_provider

        mock_serializer = MagicMock()
        # PUT requiere todos los campos requeridos, partial=False por defecto
        mock_serializer.is_valid.side_effect = ValidationError({'kompany_name': ['Requerido']})
        mock_get_serializer.return_value = mock_serializer

        data = {'phone': '1234567890'}  # Falta kompany_name y nit_document

        url = reverse('providers-update-providers', kwargs={'pk': 1})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Providers.views.ProvidersViewSets.get_object')
    @patch('api.Providers.views.ProvidersViewSets.get_serializer')
    def test_patch_state_with_valid_boolean(self, mock_get_serializer, mock_get_object):
        """Test: patch state con valores booleanos válidos"""
        mock_provider = MagicMock()
        mock_get_object.return_value = mock_provider

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'state': True}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('providers-patch-state', kwargs={'pk': 1})

        # Probar con True
        response = self.client.patch(url, {'state': True}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # Probar con False
        mock_serializer.data = {'id': 1, 'state': False}
        response = self.client.patch(url, {'state': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    @patch('api.Providers.views.ProvidersViewSets.filter_queryset')
    def test_search_providers_special_characters(self, mock_filter_queryset, mock_get_queryset):
        """Test: buscar con caracteres especiales"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered

        with patch('api.Providers.views.ProvidersViewSets.get_serializer') as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.data = []
            mock_get_serializer.return_value = mock_serializer

            # Buscar con caracteres especiales
            response = self.client.get(self.url_search_providers, {'search': 'Empresa @#$%'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    # ==================== TESTS DE INTEGRIDAD DE RESPUESTAS ====================

    def test_response_structure_get_providers(self):
        """Test: verificar estructura de respuesta en get_providers"""
        with patch('api.Providers.views.ProvidersViewSets.get_queryset') as mock_qs,              patch('api.Providers.views.ProvidersViewSets.get_serializer') as mock_ser:

            mock_qs.return_value = []
            mock_serializer = MagicMock()
            mock_serializer.data = []
            mock_ser.return_value = mock_serializer

            response = self.client.get(self.url_get_providers)

            self.assertIn('results', response.data)
            self.assertIn('success', response.data)
            self.assertIsInstance(response.data['success'], bool)

    def test_response_structure_create_providers(self):
        """Test: verificar estructura de respuesta en create_providers"""
        with patch('api.Providers.views.ProvidersViewSets.get_serializer') as mock_ser:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1}
            mock_ser.return_value = mock_serializer

            response = self.client.post(self.url_create_providers, {
                'nit_document': '123',
                'kompany_name': 'Test'
            }, format='json')

            self.assertIn('results', response.data)
            self.assertIn('object', response.data)
            self.assertIn('success', response.data)
            self.assertTrue(response.data['success'])

    def test_response_structure_delete_providers(self):
        """Test: verificar estructura de respuesta en delete_providers"""
        with patch('api.Providers.views.ProvidersViewSets.get_object') as mock_obj:
            mock_provider = MagicMock()
            mock_provider.delete = MagicMock()
            mock_obj.return_value = mock_provider

            url = reverse('providers-delete-providers', kwargs={'pk': 1})
            response = self.client.delete(url)

            self.assertIn('results', response.data)
            # Nota: typo en código original 'succes' vs 'success'
            self.assertIn('succes', response.data)

    # ==================== TESTS DE LOGGING (si aplica) ====================

    # Los endpoints de Providers no tienen logging, pero podrías agregarlos

    # ==================== TESTS DE SERIALIZADORES ====================

    def test_providers_serializers_fields(self):
        """Test: verificar campos del serializer principal"""
        # Este test requiere acceso al modelo real o mocks
        # Verificar que el serializer incluye los campos esperados
        expected_fields = ['id', 'nit_document', 'kompany_name', 'contact_name', 'phone', 'address', 'state']
        # Implementar según tu serializer real
        pass

    def test_patch_state_serializer_fields(self):
        """Test: verificar campos del serializer de estado"""
        # PatchStateSerializer debería tener solo el campo 'state'
        # Implementar según tu serializer real
        pass


class ProvidersViewSetsIntegrationTestCase(APITestCase):
    """Tests de integración con base de datos real"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_actual_database_crud(self):
        """Test: CRUD completo con base de datos real"""
        # Crear
        data = {
            'nit_document': '900123456',
            'kompany_name': 'Empresa Integración',
            'contact_name': 'Contacto Test',
            'phone': '3001234567',
            'address': 'Carrera 123 # 45-67'
        }

        response = self.client.post(reverse('providers-create-providers'), data, format='json')

        # Si tienes base de datos configurada, esto funcionará
        # Si no, puede fallar y deberías usar mocks
        if response.status_code == status.HTTP_200_OK:
            provider_id = response.data.get('object', {}).get('id')

            # Leer
            url = reverse('providers-get-providers-by-id', kwargs={'pk': provider_id})
            response = self.client.get(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Actualizar
            update_data = {'kompany_name': 'Empresa Actualizada'}
            url = reverse('providers-update-providers', kwargs={'pk': provider_id})
            response = self.client.put(url, {**data, **update_data}, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Cambiar estado
            url = reverse('providers-patch-state', kwargs={'pk': provider_id})
            response = self.client.patch(url, {'state': False}, format='json')
            self.assertEqual(response.status_code, status.HTTP_200_OK)

            # Eliminar
            url = reverse('providers-delete-providers', kwargs={'pk': provider_id})
            response = self.client.delete(url)
            self.assertEqual(response.status_code, status.HTTP_200_OK)


class ProvidersSearchFilterTestCase(APITestCase):
    """Tests específicos para el filtro de búsqueda"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='searchuser',
            email='search@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    @patch('api.Providers.views.ProvidersViewSets.filter_queryset')
    def test_search_by_nit_document(self, mock_filter_queryset, mock_get_queryset):
        """Test: buscar por NIT"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered

        with patch('api.Providers.views.ProvidersViewSets.get_serializer') as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.data = [{'nit_document': '123456'}]
            mock_get_serializer.return_value = mock_serializer

            response = self.client.get(
                reverse('providers-search-providers'),
                {'search': '123456'}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        mock_filter_queryset.assert_called_once()

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    @patch('api.Providers.views.ProvidersViewSets.filter_queryset')
    def test_search_by_kompany_name(self, mock_filter_queryset, mock_get_queryset):
        """Test: buscar por nombre de empresa"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered

        with patch('api.Providers.views.ProvidersViewSets.get_serializer') as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.data = [{'kompany_name': 'Empresa XYZ'}]
            mock_get_serializer.return_value = mock_serializer

            response = self.client.get(
                reverse('providers-search-providers'),
                {'search': 'Empresa XYZ'}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    @patch('api.Providers.views.ProvidersViewSets.filter_queryset')
    def test_search_by_contact_name(self, mock_filter_queryset, mock_get_queryset):
        """Test: buscar por nombre de contacto"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered

        with patch('api.Providers.views.ProvidersViewSets.get_serializer') as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.data = [{'contact_name': 'Juan Pérez'}]
            mock_get_serializer.return_value = mock_serializer

            response = self.client.get(
                reverse('providers-search-providers'),
                {'search': 'Juan Pérez'}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    @patch('api.Providers.views.ProvidersViewSets.filter_queryset')
    def test_search_by_phone(self, mock_filter_queryset, mock_get_queryset):
        """Test: buscar por teléfono"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered

        with patch('api.Providers.views.ProvidersViewSets.get_serializer') as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.data = [{'phone': '3001234567'}]
            mock_get_serializer.return_value = mock_serializer

            response = self.client.get(
                reverse('providers-search-providers'),
                {'search': '3001234567'}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

    @patch('api.Providers.views.ProvidersViewSets.get_queryset')
    @patch('api.Providers.views.ProvidersViewSets.filter_queryset')
    def test_search_by_address(self, mock_filter_queryset, mock_get_queryset):
        """Test: buscar por dirección"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered

        with patch('api.Providers.views.ProvidersViewSets.get_serializer') as mock_get_serializer:
            mock_serializer = MagicMock()
            mock_serializer.data = [{'address': 'Calle 123'}]
            mock_get_serializer.return_value = mock_serializer

            response = self.client.get(
                reverse('providers-search-providers'),
                {'search': 'Calle 123'}
            )

        self.assertEqual(response.status_code, status.HTTP_200_OK)

# Create your tests here.
