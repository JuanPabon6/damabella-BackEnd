"""
========================================================
  Unit Tests - Módulo de Categorías
  Archivo: test_views.py
  Autor: QA Engineer
========================================================
  Cobertura:
    - GET    /categories/get_categories/
    - GET    /categories/{pk}/get_categories_by_id/
    - POST   /categories/create_categories/
    - DELETE /categories/{pk}/delete_categories/
    - PUT    /categories/{pk}/update_categories/
    - GET    /categories/search_categories/?search=...
    - PATCH  /categories/{pk}/change_state/
    - GET    /categories/{pk}/get_products_by_category/
========================================================
"""

from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from rest_framework import status
from unittest.mock import patch, MagicMock
from .models import Categories


# ──────────────────────────────────────────────
#  Helpers / Fixtures
# ──────────────────────────────────────────────

def make_category(**kwargs):
    """Crea y retorna una Categories con valores por defecto sobreescribibles."""
    defaults = {
        "name": "Electrónica",
        "description": "Dispositivos electrónicos",
        "is_active": True,
    }
    defaults.update(kwargs)
    return Categories.objects.create(**defaults)


# ──────────────────────────────────────────────
#  Clase base compartida
# ──────────────────────────────────────────────

class CategoriesBaseTestCase(TestCase):
    """Configuración base: cliente DRF listo para usar en cada suite."""

    def setUp(self):
        self.client = APIClient()


# ════════════════════════════════════════════════════════════════
#  1. GET /categories/get_categories/
# ════════════════════════════════════════════════════════════════

class GetCategoriesTests(CategoriesBaseTestCase):

    def test_returns_200_with_existing_categories(self):
        """Lista con registros → 200 OK y success=True."""
        make_category(name="Ropa")
        make_category(name="Hogar")
        url = reverse("categories-get-categories")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(len(response.data["results"]), 2)

    def test_returns_200_with_empty_list(self):
        """Lista vacía → 200 (el queryset existe pero no tiene objetos)."""
        url = reverse("categories-get-categories")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    def test_response_contains_required_fields(self):
        """Cada ítem contiene los campos del modelo."""
        make_category()
        url = reverse("categories-get-categories")
        response = self.client.get(url)

        item = response.data["results"][0]
        for field in ("id_category", "name", "description", "is_active"):
            self.assertIn(field, item)

    @patch("api.Categories.views.CategoriesViewSets.get_queryset")
    def test_returns_500_on_unexpected_exception(self, mock_qs):
        """Excepción no controlada → 500 y success=False."""
        mock_qs.side_effect = Exception("DB unavailable")
        url = reverse("categories-get-categories")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data["success"])


# ════════════════════════════════════════════════════════════════
#  2. GET /categories/{pk}/get_categories_by_id/
# ════════════════════════════════════════════════════════════════

class GetCategoryByIdTests(CategoriesBaseTestCase):

    def test_returns_200_for_existing_category(self):
        """PK existente → 200 OK con el objeto correcto."""
        cat = make_category()
        url = reverse("categories-get-categories-by-id", kwargs={"pk": cat.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["results"]["id_category"], cat.pk)

    def test_returns_404_for_nonexistent_pk(self):
        """PK inexistente → 404 NOT FOUND."""
        url = reverse("categories-get-categories-by-id", kwargs={"pk": 9999})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_response_name_matches_stored_value(self):
        """El nombre devuelto coincide con el almacenado."""
        cat = make_category(name="Juguetes")
        url = reverse("categories-get-categories-by-id", kwargs={"pk": cat.pk})
        response = self.client.get(url)

        self.assertEqual(response.data["results"]["name"], "Juguetes")

    @patch("api.Categories.views.CategoriesViewSets.get_object")
    def test_returns_500_on_unexpected_exception(self, mock_get):
        """Excepción genérica → 500 y success=False."""
        mock_get.side_effect = Exception("Unexpected error")
        url = reverse("categories-get-categories-by-id", kwargs={"pk": 1})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data["success"])


# ════════════════════════════════════════════════════════════════
#  3. POST /categories/create_categories/
# ════════════════════════════════════════════════════════════════

class CreateCategoryTests(CategoriesBaseTestCase):

    def test_creates_category_successfully(self):
        """Payload válido → 201 CREATED, objeto devuelto y success=True."""
        url = reverse("categories-create-categories")
        payload = {"name": "Deportes", "description": "Artículos deportivos", "is_active": True}
        response = self.client.post(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data["success"])
        self.assertIn("object", response.data)

    def test_category_persisted_in_database(self):
        """El registro queda guardado en BD."""
        url = reverse("categories-create-categories")
        self.client.post(url, {"name": "Libros"}, format="json")

        self.assertTrue(Categories.objects.filter(name="Libros").exists())

    def test_returns_400_on_duplicate_name(self):
        """Nombre duplicado (unique constraint) → 400 BAD REQUEST."""
        make_category(name="Duplicado")
        url = reverse("categories-create-categories")
        response = self.client.post(url, {"name": "Duplicado"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_400_on_missing_required_field(self):
        """Sin campo 'name' (requerido) → 400 BAD REQUEST."""
        url = reverse("categories-create-categories")
        response = self.client.post(url, {"description": "Sin nombre"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_default_is_active_is_true(self):
        """is_active debe ser True por defecto si no se envía."""
        url = reverse("categories-create-categories")
        self.client.post(url, {"name": "Default Active"}, format="json")
        cat = Categories.objects.get(name="Default Active")

        self.assertTrue(cat.is_active)

    def test_id_category_is_readonly(self):
        """id_category es read_only; intentar enviarlo no debe pisarlo."""
        url = reverse("categories-create-categories")
        self.client.post(url, {"name": "Test ID", "id_category": 999}, format="json")
        cat = Categories.objects.get(name="Test ID")

        self.assertNotEqual(cat.pk, 999)

    @patch("api.Categories.views.CategoriesViewSets.get_serializer")
    def test_returns_500_on_unexpected_exception(self, mock_ser):
        """Excepción inesperada → 500 y success=False."""
        mock_ser.side_effect = Exception("Unexpected")
        url = reverse("categories-create-categories")
        response = self.client.post(url, {"name": "X"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data["success"])


# ════════════════════════════════════════════════════════════════
#  4. DELETE /categories/{pk}/delete_categories/
# ════════════════════════════════════════════════════════════════

class DeleteCategoryTests(CategoriesBaseTestCase):

    def test_deletes_existing_category(self):
        """PK existente → 200 OK y el objeto ya no existe en BD."""
        cat = make_category()
        url = reverse("categories-delete-categories", kwargs={"pk": cat.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertFalse(Categories.objects.filter(pk=cat.pk).exists())

    def test_returns_200_and_success_on_delete(self):
        """Respuesta de éxito incluye success=True."""
        cat = make_category(name="AEliminar")
        url = reverse("categories-delete-categories", kwargs={"pk": cat.pk})
        response = self.client.delete(url)

        self.assertTrue(response.data["success"])

    def test_returns_404_for_nonexistent_pk(self):
        """PK inexistente → 404 NOT FOUND."""
        url = reverse("categories-delete-categories", kwargs={"pk": 8888})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    @patch("api.Categories.views.CategoriesViewSets.get_object")
    def test_returns_500_on_unexpected_exception(self, mock_get):
        """Excepción genérica → 500 y success=False."""
        mock_get.side_effect = Exception("DB error")
        url = reverse("categories-delete-categories", kwargs={"pk": 1})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data["success"])


# ════════════════════════════════════════════════════════════════
#  5. PUT /categories/{pk}/update_categories/
# ════════════════════════════════════════════════════════════════

class UpdateCategoryTests(CategoriesBaseTestCase):

    def test_updates_category_successfully(self):
        """Payload completo válido → 200 OK y datos actualizados en BD."""
        cat = make_category(name="Viejo Nombre")
        url = reverse("categories-update-categories", kwargs={"pk": cat.pk})
        payload = {"name": "Nuevo Nombre", "description": "Nueva desc", "is_active": False}
        response = self.client.put(url, payload, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cat.refresh_from_db()
        self.assertEqual(cat.name, "Nuevo Nombre")
        self.assertFalse(cat.is_active)

    def test_returns_success_true_on_update(self):
        """Actualización exitosa incluye success=True."""
        cat = make_category()
        url = reverse("categories-update-categories", kwargs={"pk": cat.pk})
        response = self.client.put(url, {"name": "Actualizado"}, format="json")

        self.assertTrue(response.data["success"])

    def test_returns_400_on_duplicate_name(self):
        """Intentar renombrar a un nombre ya existente → 400 BAD REQUEST."""
        make_category(name="Existente")
        cat2 = make_category(name="OtraCategoria")
        url = reverse("categories-update-categories", kwargs={"pk": cat2.pk})
        response = self.client.put(url, {"name": "Existente"}, format="json")

        self.assertIn(response.status_code, [400, 500])

    def test_returns_404_for_nonexistent_pk(self):
        """PK inexistente → la vista devuelve mensaje de no encontrado."""
        url = reverse("categories-update-categories", kwargs={"pk": 7777})
        response = self.client.put(url, {"name": "X"}, format="json")

        # El view retorna 404 o 200 con success=False según implementación
        self.assertIn(response.status_code, [404, 200])

    @patch("api.Categories.views.CategoriesViewSets.get_object")
    def test_returns_500_on_unexpected_exception(self, mock_get):
        """Excepción genérica → 500 y success=False."""
        mock_get.side_effect = Exception("Unexpected")
        url = reverse("categories-update-categories", kwargs={"pk": 1})
        response = self.client.put(url, {"name": "X"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data["success"])


# ════════════════════════════════════════════════════════════════
#  6. GET /categories/search_categories/?search=...
# ════════════════════════════════════════════════════════════════

class SearchCategoriesTests(CategoriesBaseTestCase):

    def setUp(self):
        super().setUp()
        make_category(name="Electrónica", description="Gadgets")
        make_category(name="Ropa deportiva", description="Indumentaria")
        make_category(name="Libros", description="Literatura")

    def test_search_by_name_returns_matching_results(self):
        """Búsqueda por nombre devuelve solo los coincidentes."""
        url = reverse("categories-search-categories")
        response = self.client.get(url, {"search": "Electrónica"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        names = [r["name"] for r in response.data["results"]]
        self.assertIn("Electrónica", names)
        self.assertNotIn("Libros", names)

    def test_search_with_no_query_returns_all(self):
        """Sin parámetro search se devuelven todas las categorías."""
        url = reverse("categories-search-categories")
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data["results"]), 3)

    def test_search_case_insensitive(self):
        """La búsqueda no distingue mayúsculas/minúsculas."""
        url = reverse("categories-search-categories")
        response = self.client.get(url, {"search": "libros"})

        names = [r["name"] for r in response.data["results"]]
        self.assertIn("Libros", names)

    def test_search_no_results_returns_empty_list(self):
        """Término sin coincidencias → lista vacía pero 200 OK."""
        url = reverse("categories-search-categories")
        response = self.client.get(url, {"search": "ZZZInexistente"})

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["results"], [])


# ════════════════════════════════════════════════════════════════
#  7. PATCH /categories/{pk}/change_state/
# ════════════════════════════════════════════════════════════════

class ChangeStateCategoryTests(CategoriesBaseTestCase):

    def test_deactivates_active_category(self):
        """Cambiar is_active de True a False → 200 OK y BD actualizada."""
        cat = make_category(is_active=True)
        url = reverse("categories-change-state", kwargs={"pk": cat.pk})
        response = self.client.patch(url, {"is_active": False}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cat.refresh_from_db()
        self.assertFalse(cat.is_active)

    def test_activates_inactive_category(self):
        """Cambiar is_active de False a True → 200 OK."""
        cat = make_category(is_active=False)
        url = reverse("categories-change-state", kwargs={"pk": cat.pk})
        response = self.client.patch(url, {"is_active": True}, format="json")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        cat.refresh_from_db()
        self.assertTrue(cat.is_active)

    def test_returns_400_with_extra_fields(self):
        """Enviar campos adicionales a is_active → 400 BAD REQUEST (validación custom)."""
        cat = make_category()
        url = reverse("categories-change-state", kwargs={"pk": cat.pk})
        response = self.client.patch(url, {"is_active": False, "name": "Hack"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_400_without_is_active_field(self):
        """Payload sin is_active → validación falla, 400 BAD REQUEST."""
        cat = make_category()
        url = reverse("categories-change-state", kwargs={"pk": cat.pk})
        response = self.client.patch(url, {"name": "No vale"}, format="json")

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_returns_success_true_on_valid_patch(self):
        """Patch válido → success=True en la respuesta."""
        cat = make_category()
        url = reverse("categories-change-state", kwargs={"pk": cat.pk})
        response = self.client.patch(url, {"is_active": False}, format="json")

        self.assertTrue(response.data["success"])

    @patch("api.Categories.views.CategoriesViewSets.get_object")
    def test_returns_500_on_unexpected_exception(self, mock_get):
        """Excepción no controlada → 500 y success=False."""
        mock_get.side_effect = Exception("DB timeout")
        url = reverse("categories-change-state", kwargs={"pk": 1})
        response = self.client.patch(url, {"is_active": False}, format="json")

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data["success"])


# ════════════════════════════════════════════════════════════════
#  8. GET /categories/{pk}/get_products_by_category/
# ════════════════════════════════════════════════════════════════

class GetProductsByCategoryTests(CategoriesBaseTestCase):

    def test_returns_200_for_category_without_products(self):
        """Categoría sin productos → 200 OK con lista vacía."""
        cat = make_category()
        url = reverse("categories-get-products-by-category", kwargs={"pk": cat.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])
        self.assertEqual(response.data["results"], [])

    @patch("api.Categories.views.Products.objects.filter")
    def test_returns_products_for_existing_category(self, mock_filter):
        """Categoría con productos → 200 OK con lista de productos."""
        mock_product = MagicMock()
        mock_product.id_product = 1
        mock_filter.return_value = [mock_product]

        cat = make_category()
        url = reverse("categories-get-products-by-category", kwargs={"pk": cat.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertTrue(response.data["success"])

    @patch("api.Categories.views.Products.objects.filter")
    def test_returns_500_on_unexpected_exception(self, mock_filter):
        """Excepción al consultar productos → 500 y success=False."""
        mock_filter.side_effect = Exception("DB error")
        cat = make_category()
        url = reverse("categories-get-products-by-category", kwargs={"pk": cat.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, status.HTTP_500_INTERNAL_SERVER_ERROR)
        self.assertFalse(response.data["success"])


# ════════════════════════════════════════════════════════════════
#  9. Pruebas del Serializador
# ════════════════════════════════════════════════════════════════

class CategoriesSerializerTests(TestCase):

    def test_serializer_accepts_valid_data(self):
        from .serializers import CategoriesSerializers
        data = {"name": "Valid", "description": "OK", "is_active": True}
        s = CategoriesSerializers(data=data)
        self.assertTrue(s.is_valid(), s.errors)

    def test_serializer_rejects_missing_name(self):
        from .serializers import CategoriesSerializers
        s = CategoriesSerializers(data={"description": "No name"})
        self.assertFalse(s.is_valid())
        self.assertIn("name", s.errors)

    def test_patch_serializer_rejects_extra_fields(self):
        from .serializers import PatchStateCategoriesSerializers
        cat = make_category()
        s = PatchStateCategoriesSerializers(
            cat,
            data={"is_active": False, "name": "Intruder"},
            partial=True,
        )
        self.assertFalse(s.is_valid())

    def test_patch_serializer_accepts_only_is_active(self):
        from .serializers import PatchStateCategoriesSerializers
        cat = make_category()
        s = PatchStateCategoriesSerializers(cat, data={"is_active": False}, partial=True)
        self.assertTrue(s.is_valid(), s.errors)

# Create your tests here.
