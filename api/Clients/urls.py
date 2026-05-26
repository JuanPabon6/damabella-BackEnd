from rest_framework import routers
# from .views import ClientsViewSets
from django.urls import path, include

router = routers.DefaultRouter()


urlpatterns = [
    path('', include(router.urls))
]