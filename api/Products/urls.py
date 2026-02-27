from rest_framework import routers
from django.urls import path,include
from .views import ProductsViewSets,ColorViewSets,SizesViewSets, ProductPhotosViewSets, VariantProductViewSets

router = routers.DefaultRouter()
router.register(r'products', ProductsViewSets, basename='products')
router.register(r'colors', ColorViewSets, basename='colors')
router.register(r'sizes', SizesViewSets, basename='sizes')
router.register(r'photos', ProductPhotosViewSets, basename='photos')
router.register(r'variants', VariantProductViewSets, basename='variants')

urlpatterns = [
    path('', include(router.urls))
]
# from. views