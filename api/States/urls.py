from rest_framework import routers
from .views import StatesViewSets
from django.urls import path,include

router = routers.DefaultRouter()
router.register(r'states', StatesViewSets, basename='states')

urlpatterns = [
    path('', include(router.urls))
]