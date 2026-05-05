from rest_framework import routers
from django.urls import include,path
from .views import OrdersDetailsViewSet, OrdersViewSet

router = routers.DefaultRouter()

router.register(r'orders',OrdersViewSet,basename='orders')
router.register(r'ordersdetail',OrdersDetailsViewSet,basename='ordersdetail')

urlpatterns= [
path('', include(router.urls))
]