from rest_framework import routers
from django.urls import include,path
from .views import OrdersDetailsViewSet, OrdersViewSet, PaymentMethodsViewSet

router = routers.DefaultRouter()

router.register(r'orders',OrdersViewSet,basename='orders')
router.register(r'ordersdetail',OrdersDetailsViewSet,basename='ordersdetail')
router.register(r'paymentmethods', PaymentMethodsViewSet, basename='paymentmethods')

urlpatterns= [
path('', include(router.urls))
]