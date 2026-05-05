from rest_framework import routers
from .views import PurchasesViewSet, PurchaseDetailViewSet
from django.urls import path,include

router = routers.DefaultRouter()
router.register(r'purchases',PurchasesViewSet,basename='purchases')
router.register(r'purchasesdetails', PurchaseDetailViewSet, basename='purchasesdetails')

urlpatterns = [
    path('', include(router.urls))
]