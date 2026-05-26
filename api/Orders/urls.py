from rest_framework import routers
from django.urls import include,path
<<<<<<< HEAD
from .views import OrdersDetailsViewSet, OrdersViewSet
=======
from .views import OrdersDetailsViewSet, OrdersViewSet, PaymentMethodsViewSet
>>>>>>> juanjo

router = routers.DefaultRouter()

router.register(r'orders',OrdersViewSet,basename='orders')
router.register(r'ordersdetail',OrdersDetailsViewSet,basename='ordersdetail')
<<<<<<< HEAD
=======
router.register(r'paymentmethods', PaymentMethodsViewSet, basename='paymentmethods')
>>>>>>> juanjo

urlpatterns= [
path('', include(router.urls))
]