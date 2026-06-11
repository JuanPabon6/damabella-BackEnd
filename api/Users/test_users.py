from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework import status, filters, permissions
from django.contrib.auth import get_user_model
from unittest.mock import patch, MagicMock, PropertyMock, call, ANY
from datetime import datetime
import json

from api.Users.models import Users, Typesdoc, Clients
from api.Users.serializers import (
    UsersSerializer, UsersPatchActiveSerializer, TypesDocsSerializers,
    LoginSerializer, ChangePasswordSerializer, RequestOTPSerializer,
    ValidateOTPSerializer, ResetPasswordSerializer, ClientsSerializers, StateSerializer
)
from api.Users.views import (
    UsersViewSets, TypesDocsViewSets, ClientsViewSets,
    ChangePasswordView, RequestOTPView, ValidateOTPView, ResetPasswordView, LoginView
)
from api.Exceptions.exceptions import ObjectNotExists, MultiResults, IntegrityException, InvalidData
from rest_framework.exceptions import ValidationError, APIException
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned


User = get_user_model()


# =============================================================================
# TESTS PARA VISTAS DE AUTENTICACION (APIView)
# =============================================================================

class ChangePasswordViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='oldpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url = reverse('change-password')

    @patch('api.Users.views.ChangePasswordSerializer')
    def test_change_password_success(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer
        data = {'old_password': 'oldpass123', 'new_password': 'newpass123', 'confirm_password': 'newpass123'}
        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_serializer_class.assert_called_once_with(data=data, context={'request': ANY})

    @patch('api.Users.views.ChangePasswordSerializer')
    def test_change_password_invalid(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {'new_password': ['La contrasena es muy debil']}
        mock_serializer_class.return_value = mock_serializer
        response = self.client.post(self.url, {'old_password': 'wrong', 'new_password': '123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_change_password_unauthenticated(self):
        self.client.force_authenticate(user=None)
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RequestOTPViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('request-otp')

    @patch('api.Users.views.RequestOTPSerializer')
    def test_request_otp_success(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer
        response = self.client.post(self.url, {'email': 'test@example.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('enviado', response.data['message'].lower())

    @patch('api.Users.views.RequestOTPSerializer')
    def test_request_otp_invalid_email(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {'email': ['Ingrese un email valido']}
        mock_serializer_class.return_value = mock_serializer
        response = self.client.post(self.url, {'email': 'invalid'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_request_otp_no_authentication_required(self):
        response = self.client.post(self.url, {'email': 'test@example.com'}, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class ValidateOTPViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('validate-otp')

    @patch('api.Users.views.ValidateOTPSerializer')
    def test_validate_otp_success(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer
        response = self.client.post(self.url, {'email': 'test@example.com', 'otp': '123456'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('validado', response.data['message'].lower())

    @patch('api.Users.views.ValidateOTPSerializer')
    def test_validate_otp_invalid(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {'otp': ['Codigo invalido o expirado']}
        mock_serializer_class.return_value = mock_serializer
        response = self.client.post(self.url, {'email': 'test@example.com', 'otp': '000000'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class ResetPasswordViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('reset-password')

    @patch('api.Users.views.ResetPasswordSerializer')
    def test_reset_password_success(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.return_value = None
        mock_serializer_class.return_value = mock_serializer
        response = self.client.post(self.url, {'email': 'test@example.com', 'otp': '123456', 'new_password': 'newpass123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertIn('actualizada', response.data['message'].lower())

    @patch('api.Users.views.ResetPasswordSerializer')
    def test_reset_password_invalid(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {'new_password': ['La contrasena no cumple los requisitos']}
        mock_serializer_class.return_value = mock_serializer
        response = self.client.post(self.url, {}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])


class LoginViewTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.url = reverse('login')

    @patch('api.Users.views.LoginSerializer')
    def test_login_success(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.validated_data = {'access': 'fake_access_token', 'refresh': 'fake_refresh_token', 'user': {'id': 1, 'email': 'test@example.com'}}
        mock_serializer_class.return_value = mock_serializer
        response = self.client.post(self.url, {'email': 'test@example.com', 'password': 'password123'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    @patch('api.Users.views.LoginSerializer')
    def test_login_invalid_credentials(self, mock_serializer_class):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = False
        mock_serializer.errors = {'non_field_errors': ['Credenciales invalidas']}
        mock_serializer_class.return_value = mock_serializer
        response = self.client.post(self.url, {'email': 'wrong', 'password': 'wrong'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(response.data['success'])

    def test_login_no_authentication_required(self):
        response = self.client.post(self.url, {'email': 'test@test.com', 'password': '123'}, format='json')
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =============================================================================
# TESTS PARA UsersViewSets
# =============================================================================

class UsersViewSetsTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_users = reverse('users-get-users')
        self.url_create_users = reverse('users-create-users')
        self.url_search_users = reverse('users-search-users')
        self.url_export_users = reverse('users-export-users')

    def test_get_serializer_class_default(self):
        viewset = UsersViewSets()
        viewset.action = 'get_users'
        self.assertEqual(viewset.get_serializer_class(), UsersSerializer)

    def test_get_serializer_class_partial_update(self):
        viewset = UsersViewSets()
        viewset.action = 'partial_update'
        self.assertEqual(viewset.get_serializer_class(), UsersPatchActiveSerializer)

    @patch('api.Users.views.UsersViewSets.get_queryset')
    @patch('api.Users.views.UsersViewSets.get_serializer')
    def test_get_users_success(self, mock_get_serializer, mock_get_queryset):
        mock_queryset = MagicMock()
        mock_get_queryset.return_value = mock_queryset
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'name': 'Juan', 'email': 'juan@test.com'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_users)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(len(response.data['results']), 1)

    @patch('api.Users.views.UsersViewSets.get_queryset')
    def test_get_users_does_not_exist(self, mock_get_queryset):
        mock_get_queryset.side_effect = Users.DoesNotExist("No hay usuarios")
        response = self.client.get(self.url_get_users)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Users.views.UsersViewSets.get_queryset')
    def test_get_users_exception(self, mock_get_queryset):
        mock_get_queryset.side_effect = Exception('Database error')
        response = self.client.get(self.url_get_users)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.Users.views.UsersViewSets.get_object')
    @patch('api.Users.views.UsersViewSets.get_serializer')
    def test_get_users_by_id_success(self, mock_get_serializer, mock_get_object):
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'name': 'Juan'}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('users-get-users-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results']['id'], 1)

    @patch('api.Users.views.UsersViewSets.get_object')
    def test_get_users_by_id_does_not_exist(self, mock_get_object):
        mock_get_object.side_effect = Users.DoesNotExist("No existe")
        url = reverse('users-get-users-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Users.views.UsersViewSets.get_serializer')
    @patch('django.db.transaction.atomic')
    def test_create_users_success(self, mock_atomic, mock_get_serializer):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'Nuevo Usuario'}
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_users, {'name': 'Nuevo', 'email': 'nuevo@test.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 'creado exitosamente')

    @patch('api.Users.views.UsersViewSets.get_serializer')
    @patch('django.db.transaction.atomic')
    def test_create_users_integrity_error(self, mock_atomic, mock_get_serializer):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate email")
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_users, {'email': 'existing@test.com'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Users.views.UsersViewSets.get_object')
    def test_delete_users_success(self, mock_get_object):
        mock_user = MagicMock()
        mock_user.delete = MagicMock()
        mock_get_object.return_value = mock_user
        url = reverse('users-delete-users', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        mock_user.delete.assert_called_once()

    @patch('api.Users.views.UsersViewSets.get_object')
    def test_delete_users_integrity_error(self, mock_get_object):
        mock_user = MagicMock()
        mock_user.delete.side_effect = IntegrityError("Foreign key constraint")
        mock_get_object.return_value = mock_user
        url = reverse('users-delete-users', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Users.views.UsersViewSets.get_object')
    @patch('api.Users.views.UsersViewSets.get_serializer')
    def test_update_users_success(self, mock_get_serializer, mock_get_object):
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'Actualizado'}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('users-update-users', kwargs={'pk': 1})
        response = self.client.put(url, {'name': 'Actualizado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Users.views.UsersViewSets.get_object')
    @patch('api.Users.views.UsersViewSets.get_serializer')
    def test_update_users_validation_error(self, mock_get_serializer, mock_get_object):
        mock_get_object.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.is_valid.side_effect = ValidationError({'email': ['Email invalido']})
        mock_get_serializer.return_value = mock_serializer
        url = reverse('users-update-users', kwargs={'pk': 1})
        response = self.client.put(url, {'email': 'invalid'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Users.views.UsersViewSets.get_queryset')
    @patch('api.Users.views.UsersViewSets.filter_queryset')
    @patch('api.Users.views.UsersViewSets.get_serializer')
    def test_search_users_success(self, mock_get_serializer, mock_filter_queryset, mock_get_queryset):
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = True
        mock_filter_queryset.return_value = mock_filtered
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'name': 'Juan Perez'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_search_users, {'search': 'Juan'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Users.views.UsersViewSets.get_queryset')
    @patch('api.Users.views.UsersViewSets.filter_queryset')
    def test_search_users_empty(self, mock_filter_queryset, mock_get_queryset):
        mock_get_queryset.return_value = MagicMock()
        mock_filtered = MagicMock()
        mock_filtered.exists.return_value = False
        mock_filter_queryset.return_value = mock_filtered
        response = self.client.get(self.url_search_users, {'search': 'XYZ999'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(response.data['success'])
        self.assertEqual(response.data['results'], [])

    @patch('api.Users.views.UsersViewSets.get_object')
    @patch('api.Users.views.UsersViewSets.get_serializer')
    def test_change_state_success(self, mock_get_serializer, mock_get_object):
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'is_active': False}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('users-change-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'is_active': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['results'], 'estado cambiado exitosamente')

    @patch('api.Users.views.UsersViewSets.get_object')
    def test_change_state_not_found(self, mock_get_object):
        mock_get_object.side_effect = Users.DoesNotExist("No existe")
        url = reverse('users-change-state', kwargs={'pk': 999})
        response = self.client.patch(url, {'is_active': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_viewset_attributes(self):
        viewset = UsersViewSets()
        self.assertEqual(viewset.queryset.model, Users)
        self.assertEqual(viewset.serializer_class, UsersSerializer)
        self.assertEqual(viewset.required_module, 'Usuarios')
        self.assertIn(filters.SearchFilter, viewset.filter_backends)


# =============================================================================
# TESTS PARA TypesDocsViewSets
# =============================================================================

class TypesDocsViewSetsTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_types = reverse('types-docs-get-types-docs')
        self.url_create_types = reverse('types-docs-create-types-docs')

    @patch('api.Users.views.TypesDocsViewSets.get_queryset')
    @patch('api.Users.views.TypesDocsViewSets.get_serializer')
    def test_get_types_docs_success(self, mock_get_serializer, mock_get_queryset):
        mock_get_queryset.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'name': 'Cedula', 'abbreviation': 'CC'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_types)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Users.views.TypesDocsViewSets.get_object')
    @patch('api.Users.views.TypesDocsViewSets.get_serializer')
    def test_get_types_docs_by_id_success(self, mock_get_serializer, mock_get_object):
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'name': 'Cedula'}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('types-docs-get-types-docs-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Users.views.TypesDocsViewSets.get_object')
    def test_get_types_docs_by_id_not_found(self, mock_get_object):
        mock_get_object.side_effect = Typesdoc.DoesNotExist("No existe")
        url = reverse('types-docs-get-types-docs-by-id', kwargs={'pk': 999})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch('api.Users.views.TypesDocsViewSets.get_serializer')
    def test_create_types_docs_success(self, mock_get_serializer):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'NIT'}
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_types, {'name': 'NIT', 'abbreviation': 'NIT'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['success'])

    @patch('api.Users.views.TypesDocsViewSets.get_serializer')
    def test_create_types_docs_integrity_error(self, mock_get_serializer):
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.save.side_effect = IntegrityError("Duplicate")
        mock_get_serializer.return_value = mock_serializer
        response = self.client.post(self.url_create_types, {'name': 'Test'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    @patch('api.Users.views.TypesDocsViewSets.get_object')
    def test_delete_types_docs_success(self, mock_get_object):
        mock_type = MagicMock()
        mock_type.delete = MagicMock()
        mock_get_object.return_value = mock_type
        url = reverse('types-docs-delete-types-docs', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Users.views.TypesDocsViewSets.get_object')
    @patch('api.Users.views.TypesDocsViewSets.get_serializer')
    def test_update_types_docs_success(self, mock_get_serializer, mock_get_object):
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'Actualizado'}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('types-docs-update-types-docs', kwargs={'pk': 1})
        response = self.client.put(url, {'name': 'Actualizado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_types_docs_allow_any(self):
        self.client.force_authenticate(user=None)
        with patch('api.Users.views.TypesDocsViewSets.get_queryset') as mock_qs, \
             patch('api.Users.views.TypesDocsViewSets.get_serializer') as mock_ser:
            mock_qs.return_value = MagicMock()
            mock_s = MagicMock()
            mock_s.data = []
            mock_ser.return_value = mock_s
            response = self.client.get(self.url_get_types)
        self.assertNotEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


# =============================================================================
# TESTS PARA ClientsViewSets
# =============================================================================

class ClientsViewSetsTestCase(APITestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='testuser', email='test@example.com', password='testpass123'
        )
        self.client.force_authenticate(user=self.user)
        self.url_get_clients = reverse('clients-get-clients')
        self.url_create_clients = reverse('clients-create-clients')
        self.url_search_clients = reverse('clients-search-clients')

    def test_get_serializer_class_default(self):
        viewset = ClientsViewSets()
        viewset.action = 'get_clients'
        self.assertEqual(viewset.get_serializer_class(), ClientsSerializers)

    def test_get_serializer_class_patch_state(self):
        viewset = ClientsViewSets()
        viewset.action = 'patch_state'
        self.assertEqual(viewset.get_serializer_class(), StateSerializer)

    @patch('api.Users.views.ClientsViewSets.get_queryset')
    @patch('api.Users.views.ClientsViewSets.get_serializer')
    def test_get_clients_success(self, mock_get_serializer, mock_get_queryset):
        mock_get_queryset.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'name': 'Cliente A'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_get_clients)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])
        self.assertEqual(response.data['message'], 'clientes obtenidos')

    @patch('api.Users.views.ClientsViewSets.get_object')
    @patch('api.Users.views.ClientsViewSets.get_serializer')
    def test_get_clients_by_id_success(self, mock_get_serializer, mock_get_object):
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.data = {'id': 1, 'name': 'Cliente A'}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('clients-get-clients-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Users.views.ClientsViewSets.get_object')
    def test_get_clients_by_id_multiple_objects(self, mock_get_object):
        mock_get_object.side_effect = MultipleObjectsReturned("Multiples objetos")
        url = reverse('clients-get-clients-by-id', kwargs={'pk': 1})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    def test_create_clients_exception(self):
        data = {'name': 'Test', 'type_doc': 'CC', 'doc': '123'}
        response = self.client.post(self.url_create_clients, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)

    @patch('api.Users.views.ClientsViewSets.get_object')
    def test_delete_clients_success(self, mock_get_object):
        mock_client = MagicMock()
        mock_client.delete = MagicMock()
        mock_get_object.return_value = mock_client
        url = reverse('clients-delete-clients', kwargs={'pk': 1})
        response = self.client.delete(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Users.views.ClientsViewSets.get_object')
    @patch('api.Users.views.ClientsViewSets.get_serializer')
    def test_update_clients_success(self, mock_get_serializer, mock_get_object):
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'name': 'Actualizado'}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('clients-update-clients', kwargs={'pk': 1})
        response = self.client.put(url, {'name': 'Actualizado'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Users.views.ClientsViewSets.get_object')
    @patch('api.Users.views.ClientsViewSets.get_serializer')
    def test_patch_state_success(self, mock_get_serializer, mock_get_object):
        mock_get_object.return_value = MagicMock(id=1)
        mock_serializer = MagicMock()
        mock_serializer.is_valid.return_value = True
        mock_serializer.data = {'id': 1, 'state': False}
        mock_get_serializer.return_value = mock_serializer
        url = reverse('clients-patch-state', kwargs={'pk': 1})
        response = self.client.patch(url, {'state': False}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    @patch('api.Users.views.ClientsViewSets.get_queryset')
    @patch('api.Users.views.ClientsViewSets.filter_queryset')
    @patch('api.Users.views.ClientsViewSets.get_serializer')
    def test_search_clients_success(self, mock_get_serializer, mock_filter_queryset, mock_get_queryset):
        mock_get_queryset.return_value = MagicMock()
        mock_filter_queryset.return_value = MagicMock()
        mock_serializer = MagicMock()
        mock_serializer.data = [{'id': 1, 'name': 'Cliente A', 'city': 'Bogota'}]
        mock_get_serializer.return_value = mock_serializer
        response = self.client.get(self.url_search_clients, {'search': 'Bogota'})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data['success'])

    def test_clients_requires_authentication(self):
        self.client.force_authenticate(user=None)
        response = self.client.get(self.url_get_clients)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_clients_viewset_attributes(self):
        viewset = ClientsViewSets()
        self.assertEqual(viewset.queryset.model, Clients)
        self.assertEqual(viewset.serializer_class, ClientsSerializers)
        self.assertEqual(viewset.required_module, 'Clientes')
        self.assertIn(permissions.IsAuthenticated, viewset.permission_classes)

# Create your tests here.
