from django.urls import path, include
from .views import RolesViewSets
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'roles', RolesViewSets, basename='roles')

urlpatterns = [
    path('', include(router.urls))
]