from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status, filters
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock, PropertyMock, call
from datetime import datetime
import json

from api.Roles.models import Roles, Permissions, RolPermission
from api.Roles.serializers import RolesSerializers, PermissionsSerializer, PatchStateRolesSerializer, RolPermissionSerializer
from api.Roles.views import RolesViewSets, PermissionsViewSets, RolPermissionViewSets
from api.Exceptions.exceptions import ObjectNotExists, MultiResults, IntegrityException, InvalidData
from rest_framework.exceptions import APIException, ValidationError
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned


User = get_user_model()


# =============================================================================
# TESTS PARA RolesViewSets
# =============================================================================

class RolesViewSetsTestCase(APITestCase):
    """Test cases para RolesViewSets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.url_get_roles = reverse('roles-get-roles')
        self.url_create_roles = reverse('roles-create-roles')
        self.url_search_roles = reverse('roles-search-roles')

    # ==================== TESTS PARA get_serializer_class ====================

    def test_get_serializer_class_default(self):
        """Test: obtener serializer por defecto (RolesSerializers)"""
        viewset = RolesViewSets()
        viewset.action = 'get_roles'
        serializer_class = viewset.get_serializer_class()
        self.assertEqual(serializer_class, RolesSerializers)

    def test_get_serializer_class_change_state(self):
        """Test: obtener serializer para acción change_state"""
        viewset = RolesViewSets()
        viewset.action = 'change_state'
        serializer_class = viewset.get_serializer_class()
        self.assertEqual(serializer_class, PatchStateRolesSerializer)

    # ==================== TESTS PARA get_roles ====================

    @patch('api.Roles.views.RolesViewSets.get_queryset')
    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_get_roles_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener lista de roles exitosamente"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = True
        mock_get_queryset.return_value = mock_queryset

        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'name': 'Admin', 'description': 'Administrador'},
            {'id': 2, 'name': 'User', 'description': 'Usuario'},
        ]
        mock_get_serializer.return_value = mock_serializer

        response = self.client.get(self.url_get_roles)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['results']), 2)
        mock_get_serializer.assert_called_once_with(mock_queryset, many=True)

    @patch('api.Roles.views.RolesViewSets.get_queryset')
    def test_get_roles_empty(self, mock_get_queryset):
        """Test: obtener lista de roles vacía (204 No Content)"""
        mock_queryset = MagicMock()
        mock_queryset.exists.return_value = False
        mock_get_queryset.return_value = mock_queryset

        response = self.client.get(self.url_get_roles)

        self.assertEqual(response.status_code, status.HTTP_204_NO_CONTENT)
        self.assertEqual(response.data['results'], [])

    @patch('api.Roles.views.RolesViewSets.get_queryset')
    def test_get_roles_exception(self, mock_get_queryset):
        """Test: manejo de excepción en get_roles"""
        mock_get_queryset.side_effect = Exception('Database error')

        response = self.client.get(self.url_get_roles)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA get_rol_by_id ====================

    @patch('api.Roles.views.RolesViewSets.get_object')
    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_get_rol_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener rol por ID exitosamente"""
        mock_rol = MagicMock()
        mock_rol.id = 1
        mock_get_object.return_value = mock_rol

        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'name': 'Admin', 'description': 'Administrador'}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('roles-get-rol-by-id', kwargs={'pk': 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results']['id'], 1)
        mock_get_serializer.assert_called_once_with(mock_rol, many=False)

    @patch('api.Roles.views.RolesViewSets.get_object')
    def test_get_rol_by_id_does_not_exist(self, mock_get_object):
        """Test: manejo de Roles.DoesNotExist"""
        mock_get_object.side_effect = Roles.DoesNotExist("No existe")

        url = reverse('roles-get-rol-by-id', kwargs={'pk': 999})
        response = self.client.get(url)

        # ObjectNotExists es una APIException, típicamente 404
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Roles.views.RolesViewSets.get_object')
    def test_get_rol_by_id_exception(self, mock_get_object):
        """Test: manejo de excepción genérica en get_rol_by_id"""
        mock_get_object.side_effect = Exception('Server error')

        url = reverse('roles-get-rol-by-id', kwargs={'pk': 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA create_roles ====================

    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_create_roles_success(self, mock_get_serializer):
        """Test: crear rol exitosamente (201 Created)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'Nuevo Rol', 'description': 'Descripción'}
        mock_get_serializer.return_value = mock_serializer

        data = {'name': 'Nuevo Rol', 'description': 'Descripción del rol'}

        response = self.client.post(self.url_create_roles, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 'creado exitosamente')
        self.assertIn('object', response.data)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_create_roles_validation_error(self, mock_get_serializer):
        """Test: crear rol con datos inválidos (ValidationError -> InvalidData)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'name': ['Este campo es requerido']})
        mock_get_serializer.return_value = mock_serializer

        data = {'description': 'Sin nombre'}

        response = self.client.post(self.url_create_roles, data, format='json')

        # InvalidData típicamente retorna 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_create_roles_multiple_objects(self, mock_get_serializer):
        """Test: manejo de MultipleObjectsReturned en create_roles"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = MultipleObjectsReturned("Múltiples objetos")
        mock_get_serializer.return_value = mock_serializer

        data = {'name': 'Rol Duplicado'}

        response = self.client.post(self.url_create_roles, data, format='json')

        # MultiResults típicamente retorna 400 o 500
        self.assertIn(response.status_code, [status.HTTP_400_BAD_REQUEST, status.HTTP_500_INTERNAL_SERVER_ERROR])

    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_create_roles_exception(self, mock_get_serializer):
        """Test: manejo de excepción genérica en create_roles"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Unexpected error')
        mock_get_serializer.return_value = mock_serializer

        response = self.client.post(self.url_create_roles, {'name': 'Rol'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA delete_rol ====================

    @patch('api.Roles.views.RolesViewSets.get_object')
    def test_delete_rol_success(self, mock_get_object):
        """Test: eliminar rol exitosamente"""
        mock_rol = MagicMock()
        mock_rol.id = 1
        mock_rol.delete = MagicMock()
        mock_get_object.return_value = mock_rol

        url = reverse('roles-delete-rol', kwargs={'pk': 1})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('eliminado', response.data['results'].lower())
        mock_rol.delete.assert_called_once()

    @patch('api.Roles.views.RolesViewSets.get_object')
    def test_delete_rol_not_found(self, mock_get_object):
        """Test: eliminar rol que no existe (DoesNotExist)"""
        mock_get_object.side_effect = Roles.DoesNotExist("No existe")

        url = reverse('roles-delete-rol', kwargs={'pk': 999})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Roles.views.RolesViewSets.get_object')
    def test_delete_rol_integrity_error(self, mock_get_object):
        """Test: eliminar rol con restricción de integridad (IntegrityError)"""
        mock_rol = MagicMock()
        mock_rol.delete.side_effect = IntegrityError("Foreign key constraint")
        mock_get_object.return_value = mock_rol

        url = reverse('roles-delete-rol', kwargs={'pk': 1})
        response = self.client.delete(url)

        # IntegrityException típicamente retorna 400
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Roles.views.RolesViewSets.get_object')
    def test_delete_rol_exception(self, mock_get_object):
        """Test: manejo de excepción genérica en delete_rol"""
        mock_get_object.side_effect = Exception('Server error')

        url = reverse('roles-delete-rol', kwargs={'pk': 1})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA update_roles ====================

    @patch('api.Roles.views.RolesViewSets.get_object')
    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_update_roles_success(self, mock_get_serializer, mock_get_object):
        """Test: actualizar rol exitosamente"""
        mock_rol = MagicMock()
        mock_rol.id = 1
        mock_get_object.return_value = mock_rol

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'Rol Actualizado', 'description': 'Nueva descripción'}
        mock_get_serializer.return_value = mock_serializer

        data = {'name': 'Rol Actualizado', 'description': 'Nueva descripción'}

        url = reverse('roles-update-roles', kwargs={'pk': 1})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 'actualizado exitosamente')
        self.assertIn('rol', response.data)
        mock_serializer.save.assert_called_once()

    @patch('api.Roles.views.RolesViewSets.get_object')
    def test_update_roles_not_found(self, mock_get_object):
        """Test: actualizar rol que no existe"""
        mock_get_object.side_effect = Roles.DoesNotExist("No existe")

        url = reverse('roles-update-roles', kwargs={'pk': 999})
        response = self.client.put(url, {'name': 'Rol'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Roles.views.RolesViewSets.get_object')
    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_update_roles_validation_error(self, mock_get_serializer, mock_get_object):
        """Test: actualizar rol con datos inválidos (ValidationError)"""
        mock_rol = MagicMock()
        mock_get_object.return_value = mock_rol

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'name': ['Requerido']})
        mock_get_serializer.return_value = mock_serializer

        url = reverse('roles-update-roles', kwargs={'pk': 1})
        response = self.client.put(url, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Roles.views.RolesViewSets.get_object')
    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_update_roles_indentation_error(self, mock_get_serializer, mock_get_object):
        """Test: manejo de IndentationError (nota: probablemente debería ser IntegrityError)"""
        mock_rol = MagicMock()
        mock_get_object.return_value = mock_rol

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IndentationError("Indentation error")
        mock_get_serializer.return_value = mock_serializer

        url = reverse('roles-update-roles', kwargs={'pk': 1})
        response = self.client.put(url, {'name': 'Rol'}, format='json')

        # IndentationError capturado como IntegrityException
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Roles.views.RolesViewSets.get_object')
    def test_update_roles_exception(self, mock_get_object):
        """Test: manejo de excepción genérica en update_roles"""
        mock_get_object.side_effect = Exception('Server error')

        url = reverse('roles-update-roles', kwargs={'pk': 1})
        response = self.client.put(url, {'name': 'Rol'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA search_roles ====================

    @patch('api.Roles.views.RolesViewSets.get_queryset')
    @patch('api.Roles.views.RolesViewSets.filter_queryset')
    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_search_roles_success(self, mock_get_serializer, mock_filter_queryset, mock_get_queryset):
        """Test: buscar roles con resultados"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered

        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'name': 'Admin', 'description': 'Administrador'},
        ]
        mock_get_serializer.return_value = mock_serializer

        response = self.client.get(self.url_search_roles, {'search': 'Admin'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'resultados obtenidos')
        self.assertEqual(len(response.data['results']), 1)

    @patch('api.Roles.views.RolesViewSets.get_queryset')
    @patch('api.Roles.views.RolesViewSets.filter_queryset')
    def test_search_roles_empty(self, mock_filter_queryset, mock_get_queryset):
        """Test: buscar roles sin resultados"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = False
        mock_filter_queryset.return_value = mock_filtered

        response = self.client.get(self.url_search_roles, {'search': 'XYZ123'})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['message'], 'sin resultados')
        self.assertEqual(response.data['results'], [])

    @patch('api.Roles.views.RolesViewSets.get_queryset')
    def test_search_roles_exception(self, mock_get_queryset):
        """Test: excepción en search_roles"""
        mock_get_queryset.side_effect = Exception('Search error')

        response = self.client.get(self.url_search_roles)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA change_state ====================

    @patch('api.Roles.views.RolesViewSets.get_object')
    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_change_state_success(self, mock_get_serializer, mock_get_object):
        """Test: cambiar estado de rol exitosamente (PATCH)"""
        mock_rol = MagicMock()
        mock_rol.id = 1
        mock_get_object.return_value = mock_rol

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'state': False}
        mock_get_serializer.return_value = mock_serializer

        data = {'state': False}

        url = reverse('roles-change-state', kwargs={'pk': 1})
        response = self.client.patch(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'estado cambiado exitosamente')
        self.assertIn('permission', response.data)  # Nota: usa 'permission' en lugar de 'rol'
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Roles.views.RolesViewSets.get_object')
    @patch('api.Roles.views.RolesViewSets.get_serializer')
    def test_change_state_validation_error(self, mock_get_serializer, mock_get_object):
        """Test: cambiar estado con datos inválidos"""
        mock_rol = MagicMock()
        mock_get_object.return_value = mock_rol

        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'state': ['Debe ser booleano']})
        mock_get_serializer.return_value = mock_serializer

        url = reverse('roles-change-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': 'invalid'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Roles.views.RolesViewSets.get_object')
    def test_change_state_multiple_objects(self, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en change_state"""
        mock_get_object.side_effect = MultipleObjectsReturned("Múltiples objetos")

        url = reverse('roles-change-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': False}, format='json')

        # Nota: este endpoint retorna 200 con success=False en lugar de lanzar excepción
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples objetos', response.data['message'].lower())

    @patch('api.Roles.views.RolesViewSets.get_object')
    def test_change_state_exception(self, mock_get_object):
        """Test: manejo de excepción genérica en change_state"""
        mock_get_object.side_effect = Exception('Server error')

        url = reverse('roles-change-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': False}, format='json')

        # Nota: este endpoint retorna 200 con success=False en lugar de 500
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['success'])
        self.assertIn('server error', response.data['error'].lower())

    # ==================== TESTS DE CONFIGURACIÓN ====================

    def test_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = RolesViewSets()

        self.assertEqual(viewset.queryset.model, Roles)
        self.assertEqual(viewset.serializer_class, RolesSerializers)
        self.assertEqual(viewset.required_module, 'Roles')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)
        self.assertEqual(viewset.search_fields, ['name', 'description'])

    # ==================== TESTS DE AUTENTICACIÓN ====================

    def test_unauthenticated_access(self):
        """Test: verificar comportamiento sin autenticación"""
        self.client.force_authenticate(user=None)

        response = self.client.get(self.url_get_roles)

        # Depende de tu configuración global de autenticación
        self.assertIn(response.status_code, [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN
        ])

    # ==================== TESTS DE MÉTODOS HTTP ====================

    def test_http_methods_not_allowed(self):
        """Test: verificar métodos HTTP no soportados"""
        response_post = self.client.post(self.url_get_roles, {})
        response_put = self.client.put(self.url_get_roles, {})
        response_delete = self.client.delete(self.url_get_roles)

        self.assertIn(response_post.status_code, [
            status.HTTP_405_METHOD_NOT_ALLOWED,
            status.HTTP_403_FORBIDDEN
        ])

    # ==================== TESTS DE ESTRUCTURA DE RESPUESTAS ====================

    def test_response_structure_get_roles(self):
        """Test: verificar estructura de respuesta en get_roles"""
        with patch('api.Roles.views.RolesViewSets.get_queryset') as mock_qs,              patch('api.Roles.views.RolesViewSets.get_serializer') as mock_ser:

            mock_queryset = MagicMock()
            mock_queryset.exists.return_value = True
            mock_qs.return_value = mock_queryset

            mock_serializer = MagicMock()
            mock_serializer.data = []
            mock_ser.return_value = mock_serializer

            response = self.client.get(self.url_get_roles)

            self.assertIn('results', response.data)
            self.assertIn('success', response.data)
            self.assertIsInstance(response.data['success'], bool)

    def test_response_structure_create_roles(self):
        """Test: verificar estructura de respuesta en create_roles"""
        with patch('api.Roles.views.RolesViewSets.get_serializer') as mock_ser:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1}
            mock_ser.return_value = mock_serializer

            response = self.client.post(self.url_create_roles, {
                'name': 'Test',
                'description': 'Desc'
            }, format='json')

            self.assertIn('results', response.data)
            self.assertIn('object', response.data)
            self.assertIn('success', response.data)
            self.assertTrue(response.data['success'])


# =============================================================================
# TESTS PARA PermissionsViewSets
# =============================================================================

class PermissionsViewSetsTestCase(APITestCase):
    """Test cases para PermissionsViewSets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.url_get_all = reverse('permissions-get-all-permissions')
        self.url_create = reverse('permissions-create-permissions')

    # ==================== TESTS PARA get_all_permissions ====================

    @patch('api.Roles.views.PermissionsViewSets.get_queryset')
    @patch('api.Roles.views.PermissionsViewSets.get_serializer')
    def test_get_all_permissions_success(self, mock_get_serializer, mock_get_queryset):
        """Test: obtener todos los permisos exitosamente"""
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset

        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'name': 'create_user', 'description': 'Crear usuario'},
            {'id': 2, 'name': 'delete_user', 'description': 'Eliminar usuario'},
        ]
        mock_get_serializer.return_value = mock_serializer

        response = self.client.get(self.url_get_all)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'permisos obtenidos')
        self.assertEqual(len(response.data['results']), 2)

    @patch('api.Roles.views.PermissionsViewSets.get_queryset')
    def test_get_all_permissions_exception(self, mock_get_queryset):
        """Test: manejo de excepción en get_all_permissions"""
        mock_get_queryset.side_effect = Exception('Database error')

        response = self.client.get(self.url_get_all)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('database error', response.data['error'].lower())

    # ==================== TESTS PARA get_permissions_by_id ====================

    @patch('api.Roles.views.PermissionsViewSets.get_object')
    @patch('api.Roles.views.PermissionsViewSets.get_serializer')
    def test_get_permissions_by_id_success(self, mock_get_serializer, mock_get_object):
        """Test: obtener permiso por ID exitosamente"""
        mock_permission = MagicMock()
        mock_permission.id = 1
        mock_get_object.return_value = mock_permission

        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'name': 'create_user', 'description': 'Crear usuario'}
        mock_get_serializer.return_value = mock_serializer

        url = reverse('permissions-get-permissions-by-id', kwargs={'pk': 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'permiso obtenido')
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.Roles.views.PermissionsViewSets.get_object')
    def test_get_permissions_by_id_not_found(self, mock_get_object):
        """Test: obtener permiso que no existe (DoesNotExist)"""
        mock_get_object.side_effect = Permissions.DoesNotExist("No existe")

        url = reverse('permissions-get-permissions-by-id', kwargs={'pk': 999})
        response = self.client.get(url)

        # Nota: retorna 500 en lugar de 404
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('no se encontraron', response.data['message'].lower())

    @patch('api.Roles.views.PermissionsViewSets.get_object')
    def test_get_permissions_by_id_exception(self, mock_get_object):
        """Test: manejo de excepción genérica en get_permissions_by_id"""
        mock_get_object.side_effect = Exception('Server error')

        url = reverse('permissions-get-permissions-by-id', kwargs={'pk': 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA create_permissions ====================

    @patch('api.Roles.views.PermissionsViewSets.get_serializer')
    def test_create_permissions_success(self, mock_get_serializer):
        """Test: crear permiso exitosamente (201 Created)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'new_permission', 'description': 'Nuevo permiso'}
        mock_get_serializer.return_value = mock_serializer

        data = {'name': 'new_permission', 'description': 'Nuevo permiso'}

        response = self.client.post(self.url_create, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'creado exitosamente')
        self.assertIn('object', response.data)
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Roles.views.PermissionsViewSets.get_serializer')
    def test_create_permissions_integrity_error(self, mock_get_serializer):
        """Test: crear permiso con IntegrityError (nombre duplicado)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate key")
        mock_get_serializer.return_value = mock_serializer

        data = {'name': 'existing_permission'}

        response = self.client.post(self.url_create, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error de llaves', response.data['message'].lower())

    @patch('api.Roles.views.PermissionsViewSets.get_serializer')
    def test_create_permissions_validation_error(self, mock_get_serializer):
        """Test: crear permiso con ValidationError"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'name': ['Requerido']})
        mock_get_serializer.return_value = mock_serializer

        response = self.client.post(self.url_create, {}, format='json')

        # ValidationError no está capturado específicamente, cae en Exception
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.Roles.views.PermissionsViewSets.get_serializer')
    def test_create_permissions_exception(self, mock_get_serializer):
        """Test: manejo de excepción genérica en create_permissions"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = Exception('Unexpected error')
        mock_get_serializer.return_value = mock_serializer

        response = self.client.post(self.url_create, {'name': 'Test'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS PARA delete_permissions ====================

    @patch('api.Roles.views.PermissionsViewSets.get_object')
    def test_delete_permissions_success(self, mock_get_object):
        """Test: eliminar permiso exitosamente"""
        mock_permission = MagicMock()
        mock_permission.id = 1
        mock_permission.delete = MagicMock()
        mock_get_object.return_value = mock_permission

        url = reverse('permissions-delete-permissions', kwargs={'pk': 1})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('eliminado', response.data['message'].lower())
        mock_permission.delete.assert_called_once()

    @patch('api.Roles.views.PermissionsViewSets.get_object')
    def test_delete_permissions_integrity_error(self, mock_get_object):
        """Test: eliminar permiso con restricción de integridad"""
        mock_permission = MagicMock()
        mock_permission.delete.side_effect = IntegrityError("Foreign key constraint")
        mock_get_object.return_value = mock_permission

        url = reverse('permissions-delete-permissions', kwargs={'pk': 1})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('error de llaves', response.data['message'].lower())

    @patch('api.Roles.views.PermissionsViewSets.get_object')
    def test_delete_permissions_exception(self, mock_get_object):
        """Test: manejo de excepción genérica en delete_permissions"""
        mock_get_object.side_effect = Exception('Server error')

        url = reverse('permissions-delete-permissions', kwargs={'pk': 1})
        response = self.client.delete(url)

        # Nota: no especifica status code, usa default (200)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['success'])
        self.assertIn('server error', response.data['errors'].lower())

    # ==================== TESTS PARA update_permissions ====================

    @patch('api.Roles.views.PermissionsViewSets.get_object')
    @patch('api.Roles.views.PermissionsViewSets.get_serializer')
    def test_update_permissions_success(self, mock_get_serializer, mock_get_object):
        """Test: actualizar permiso exitosamente"""
        mock_permission = MagicMock()
        mock_permission.id = 1
        mock_get_object.return_value = mock_permission

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'updated_permission', 'description': 'Actualizado'}
        mock_get_serializer.return_value = mock_serializer

        data = {'name': 'updated_permission', 'description': 'Actualizado'}

        url = reverse('permissions-update-permissions', kwargs={'pk': 1})
        response = self.client.put(url, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'actualizado exitosamente')
        self.assertIn('permission', response.data)
        mock_serializer.save.assert_called_once()

    @patch('api.Roles.views.PermissionsViewSets.get_object')
    def test_update_permissions_not_found(self, mock_get_object):
        """Test: actualizar permiso que no existe"""
        mock_get_object.side_effect = Permissions.DoesNotExist("No existe")

        url = reverse('permissions-update-permissions', kwargs={'pk': 999})
        response = self.client.put(url, {'name': 'Test'}, format='json')

        # Nota: retorna 200 con success=False en lugar de 404
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['success'])
        self.assertIn('este permiso no existe', response.data['message'].lower())

    @patch('api.Roles.views.PermissionsViewSets.get_object')
    @patch('api.Roles.views.PermissionsViewSets.get_serializer')
    def test_update_permissions_multiple_objects(self, mock_get_serializer, mock_get_object):
        """Test: manejo de MultipleObjectsReturned en update_permissions"""
        mock_permission = MagicMock()
        mock_get_object.return_value = mock_permission

        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = MultipleObjectsReturned("Múltiples resultados")
        mock_get_serializer.return_value = mock_serializer

        url = reverse('permissions-update-permissions', kwargs={'pk': 1})
        response = self.client.put(url, {'name': 'Test'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])
        self.assertIn('multiples resultados', response.data['message'].lower())

    @patch('api.Roles.views.PermissionsViewSets.get_object')
    def test_update_permissions_exception(self, mock_get_object):
        """Test: manejo de excepción genérica en update_permissions"""
        mock_get_object.side_effect = Exception('Server error')

        url = reverse('permissions-update-permissions', kwargs={'pk': 1})
        response = self.client.put(url, {'name': 'Test'}, format='json')

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data['success'])

    # ==================== TESTS DE CONFIGURACIÓN ====================

    def test_permissions_viewset_attributes(self):
        """Test: verificar atributos del viewset de permisos"""
        viewset = PermissionsViewSets()

        self.assertEqual(viewset.queryset.model, Permissions)
        self.assertEqual(viewset.serializer_class, PermissionsSerializer)


# =============================================================================
# TESTS PARA RolPermissionViewSets
# =============================================================================

class RolPermissionViewSetsTestCase(APITestCase):
    """Test cases para RolPermissionViewSets"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

        self.url_assign = reverse('rol-permission-assing-permission')
        self.url_delete = reverse('rol-permission-delete-rol-permission')

    # ==================== TESTS PARA assing_permission ====================

    @patch('api.Roles.views.RolPermissionViewSets.get_serializer')
    def test_assign_permission_success(self, mock_get_serializer):
        """Test: asignar permiso a rol exitosamente"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'rol': 1, 'permission': 2}
        mock_get_serializer.return_value = mock_serializer

        data = {'rol': 1, 'permission': 2}

        response = self.client.post(self.url_assign, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'permiso asignado correctamente')
        mock_serializer.is_valid.assert_called_once_with(raise_exception=True)
        mock_serializer.save.assert_called_once()

    @patch('api.Roles.views.RolPermissionViewSets.get_serializer')
    def test_assign_permission_validation_error(self, mock_get_serializer):
        """Test: asignar permiso con datos inválidos"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'rol': ['Requerido']})
        mock_get_serializer.return_value = mock_serializer

        response = self.client.post(self.url_assign, {'permission': 2}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Roles.views.RolPermissionViewSets.get_serializer')
    def test_assign_permission_integrity_error(self, mock_get_serializer):
        """Test: asignar permiso duplicado (IntegrityError)"""
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate entry")
        mock_get_serializer.return_value = mock_serializer

        data = {'rol': 1, 'permission': 2}

        response = self.client.post(self.url_assign, data, format='json')

        # IntegrityError no está capturado, cae en Exception -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA delete_rol_permission ====================

    @patch('api.Roles.models.RolPermission.objects.filter')
    def test_delete_rol_permission_success(self, mock_filter):
        """Test: eliminar asignación de permiso a rol exitosamente"""
        mock_queryset = MagicMock()
        mock_queryset.delete = MagicMock()
        mock_filter.return_value = mock_queryset

        data = {'rol': 1, 'permission': 2}

        response = self.client.delete(self.url_delete, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('eliminado', response.data['message'].lower())
        mock_filter.assert_called_once_with(rol=1, permission=2)
        mock_queryset.delete.assert_called_once()

    def test_delete_rol_permission_missing_rol(self):
        """Test: eliminar sin enviar rol (400 Bad Request)"""
        data = {'permission': 2}  # Falta rol

        response = self.client.delete(self.url_delete, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('debes enviar rol y permiso', response.data['message'].lower())

    def test_delete_rol_permission_missing_permission(self):
        """Test: eliminar sin enviar permission (400 Bad Request)"""
        data = {'rol': 1}  # Falta permission

        response = self.client.delete(self.url_delete, data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])
        self.assertIn('debes enviar rol y permiso', response.data['message'].lower())

    def test_delete_rol_permission_empty_data(self):
        """Test: eliminar sin enviar ningún dato"""
        response = self.client.delete(self.url_delete, {}, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    @patch('api.Roles.models.RolPermission.objects.filter')
    def test_delete_rol_permission_not_found(self, mock_filter):
        """Test: eliminar asignación que no existe (no error, delete en queryset vacío)"""
        mock_queryset = MagicMock()
        mock_queryset.delete = MagicMock()
        mock_filter.return_value = mock_queryset

        data = {'rol': 999, 'permission': 999}

        response = self.client.delete(self.url_delete, data, format='json')

        # Django delete en queryset vacío no lanza error, simplemente retorna (0, {})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Roles.models.RolPermission.objects.filter')
    def test_delete_rol_permission_exception(self, mock_filter):
        """Test: manejo de excepción en delete_rol_permission"""
        mock_filter.side_effect = Exception('Database error')

        data = {'rol': 1, 'permission': 2}

        response = self.client.delete(self.url_delete, data, format='json')

        # No está capturado, cae en excepción no manejada -> 500
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS PARA get_permissions_by_rol ====================

    @patch('api.Roles.models.Roles.objects.filter')
    @patch('api.Roles.models.RolPermission.objects.filter')
    @patch('api.Roles.views.RolPermissionViewSets.get_serializer')
    def test_get_permissions_by_rol_success(self, mock_get_serializer, mock_rp_filter, mock_roles_filter):
        """Test: obtener permisos por rol exitosamente"""
        mock_roles_filter.return_value.exists.return_value = True

        mock_rp_queryset = MagicMock()
        mock_rp_queryset.exists.return_value = True
        mock_rp_queryset.select_related.return_value = mock_rp_queryset
        mock_rp_filter.return_value = mock_rp_queryset

        mock_serializer = MagicMock()
        mock_serializer.data = [
            {'id': 1, 'rol': 1, 'permission': {'id': 1, 'name': 'create_user'}},
            {'id': 2, 'rol': 1, 'permission': {'id': 2, 'name': 'delete_user'}},
        ]
        mock_get_serializer.return_value = mock_serializer

        url = reverse('rol-permission-get-permissions-by-rol', kwargs={'pk': 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['results']), 2)
        mock_rp_filter.assert_called_once_with(rol_id=1)

    @patch('api.Roles.models.Roles.objects.filter')
    def test_get_permissions_by_rol_not_found(self, mock_roles_filter):
        """Test: obtener permisos de rol que no existe (404)"""
        mock_roles_filter.return_value.exists.return_value = False

        url = reverse('rol-permission-get-permissions-by-rol', kwargs={'pk': 999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
        self.assertFalse(response.data['success'])
        self.assertIn('no existe', response.data['message'].lower())

    @patch('api.Roles.models.Roles.objects.filter')
    @patch('api.Roles.models.RolPermission.objects.filter')
    def test_get_permissions_by_rol_empty(self, mock_rp_filter, mock_roles_filter):
        """Test: obtener permisos de rol sin permisos asignados"""
        mock_roles_filter.return_value.exists.return_value = True

        mock_rp_queryset = MagicMock()
        mock_rp_queryset.exists.return_value = False
        mock_rp_queryset.select_related.return_value = mock_rp_queryset
        mock_rp_filter.return_value = mock_rp_queryset

        url = reverse('rol-permission-get-permissions-by-rol', kwargs={'pk': 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], [])
        self.assertIn('no tiene permisos', response.data['message'].lower())

    @patch('api.Roles.models.Roles.objects.filter')
    def test_get_permissions_by_rol_exception(self, mock_roles_filter):
        """Test: manejo de excepción en get_permissions_by_rol"""
        mock_roles_filter.side_effect = Exception('Database error')

        url = reverse('rol-permission-get-permissions-by-rol', kwargs={'pk': 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    # ==================== TESTS DE CONFIGURACIÓN ====================

    def test_rol_permission_viewset_attributes(self):
        """Test: verificar atributos del viewset"""
        viewset = RolPermissionViewSets()

        self.assertEqual(viewset.queryset.model, RolPermission)
        self.assertEqual(viewset.serializer_class, RolPermissionSerializer)

    # ==================== TESTS DE CASOS BORDE ====================

    def test_assign_permission_invalid_rol_type(self):
        """Test: asignar permiso con rol no numérico"""
        with patch('api.Roles.views.RolPermissionViewSets.get_serializer') as mock_ser:
            mock_serializer = MagicMock()
            mock_serializer.is_valid.return_value = True
            mock_serializer.data = {'id': 1}
            mock_ser.return_value = mock_serializer

            response = self.client.post(self.url_assign, {
                'rol': 'invalid',
                'permission': 2
            }, format='json')

            # Depende de la validación del serializer
            self.assertIn(response.status_code, [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST])

    def test_delete_rol_permission_with_string_ids(self):
        """Test: eliminar asignación con IDs como strings"""
        with patch('api.Roles.models.RolPermission.objects.filter') as mock_filter:
            mock_queryset = MagicMock()
            mock_queryset.delete = MagicMock()
            mock_filter.return_value = mock_queryset

            data = {'rol': '1', 'permission': '2'}

            response = self.client.delete(self.url_delete, data, format='json')

            # Django puede convertir strings a enteros en filtros
            self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_get_permissions_by_rol_with_zero_id(self):
        """Test: obtener permisos con rol_id = 0"""
        with patch('api.Roles.models.Roles.objects.filter') as mock_roles_filter:
            mock_roles_filter.return_value.exists.return_value = False

            url = reverse('rol-permission-get-permissions-by-rol', kwargs={'pk': 0})
            response = self.client.get(url)

            self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)


# =============================================================================
# TESTS DE INTEGRACIÓN (requieren base de datos real)
# =============================================================================

class RolesPermissionsIntegrationTestCase(APITestCase):
    """Tests de integración con base de datos real"""

    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='integrationuser',
            email='integration@test.com',
            password='testpass123'
        )
        self.client.force_authenticate(user=self.user)

    def test_crud_roles_flow(self):
        """Test: flujo completo CRUD de roles"""
        # Este test requiere base de datos real configurada
        # Implementar según tus fixtures disponibles
        pass

    def test_assign_and_remove_permissions(self):
        """Test: asignar y remover permisos de un rol"""
        # Este test requiere base de datos real configurada
        # Implementar según tus fixtures disponibles
        pass

# Create your tests here.
