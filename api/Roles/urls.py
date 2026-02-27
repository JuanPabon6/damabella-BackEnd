from django.urls import path, include
from .views import RolesViewSets, PermissionsViewSets
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'roles', RolesViewSets, basename='roles')
router.register(r'permissions', PermissionsViewSets, basename='permissions')

urlpatterns = [
    path('', include(router.urls))
]