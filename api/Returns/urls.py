from rest_framework import routers
from .views import ReturnsViewSets, ReturnDetailViewsets, ChangesViewSets, ChangesDetailViewsets
from django.urls import path, include

router = routers.DefaultRouter()

router.register(r'returns', ReturnsViewSets, basename='returns')
router.register(r'returnsdetail', ReturnDetailViewsets, basename='return-detail')
router.register(r'changes', ChangesViewSets, basename='changes')
router.register(r'changesdetail', ChangesDetailViewsets, basename='changes-detail')

urlpatterns = [
    path('', include(router.urls))
]