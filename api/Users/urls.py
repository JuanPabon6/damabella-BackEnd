from rest_framework import routers
from django.urls import path,include
from .views import UsersViewSets, TypesDocsViewSets,LoginView, ChangePasswordView, RequestOTPView, ValidateOTPView, ResetPasswordView
from rest_framework_simplejwt.views import TokenRefreshView

router = routers.DefaultRouter()

router.register(r'users', UsersViewSets, basename='users')
router.register(r'typesDocs', TypesDocsViewSets, basename='typesDocs')

urlpatterns =[
    path('', include(router.urls)),
    path('auth/login/',   LoginView.as_view(),       name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/change-password/',  ChangePasswordView.as_view(), name='change_password'),
    path('auth/request-otp/',      RequestOTPView.as_view(),     name='request_otp'),
    path('auth/validate-otp/',     ValidateOTPView.as_view(),    name='validate_otp'),
    path('auth/reset-password/',   ResetPasswordView.as_view(),  name='reset_password'),
]