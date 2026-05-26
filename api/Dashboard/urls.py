from rest_framework import routers
from django.urls import path,include
from .views import DashboardViewSets

router = routers.DefaultRouter()

router.register(r'dashboard',DashboardViewSets,basename='dashboard')

urlpatterns =[
    path('', include(router.urls))
]