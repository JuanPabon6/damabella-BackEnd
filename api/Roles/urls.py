from django.urls import path, include
from .views import RolesViewSets
from rest_framework import routers

router = routers.DefaultRouter()
router.register(r'', RolesViewSets)

urlpatterns = [
    path('', include(router.urls))
]