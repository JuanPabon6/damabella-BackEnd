from rest_framework import routers
from .views import ClientsViewSets
from django.urls import path, include

router = routers.DefaultRouter()
router.register(r'clients', ClientsViewSets, basename='clients')

urlpatterns = [
    path('', include(router.urls))
]