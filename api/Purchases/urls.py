from rest_framework import routers
from .views import PurchasesViewSet, PurchaseDetailViewSet, IvaViewSets
from django.urls import path,include

router = routers.DefaultRouter()
router.register(r'purchases',PurchasesViewSet,basename='purchases')
router.register(r'purchasesdetails', PurchaseDetailViewSet, basename='purchasesdetails')
router.register(r'iva', IvaViewSets, basename='iva')

urlpatterns = [
    path('', include(router.urls))
]