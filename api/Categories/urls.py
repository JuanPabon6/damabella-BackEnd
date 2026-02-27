from rest_framework import routers
from django.urls import path,include
from .views import CategoriesViewSets

router = routers.DefaultRouter()
router.register(r'categories', CategoriesViewSets, basename='categories')

urlpatterns = [
    path('', include(router.urls))
]