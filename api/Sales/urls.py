from rest_framework import routers
from django.urls import path,include
from .views import SalesDetailViewsets,SalesViewSets

router = routers.DefaultRouter()

router.register(r'sales', SalesViewSets, basename='sales')
router.register(r'salesdetails', SalesDetailViewsets, basename='salesdetails')

urlpatterns = [
    path('', include(router.urls))
]