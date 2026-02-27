from rest_framework import routers
from django.urls import path, include
from .views import InventoryViewSets

router = routers.DefaultRouter()
router.register(r'inventory', InventoryViewSets, basename='inventory')

urlpatterns = [
    path('', include(router.urls))
]