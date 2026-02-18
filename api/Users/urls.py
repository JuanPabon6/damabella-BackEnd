from rest_framework import routers
from django.urls import path,include
from .views import UsersViewSets

router = routers.DefaultRouter()

router.register(r'', UsersViewSets)

urlpatterns =[
    path('', include(router.urls))
]