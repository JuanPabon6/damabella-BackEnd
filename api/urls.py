from django.urls import path,include

urlpatterns = [
    path('roles/', include('api.Roles.urls')),
    path('users/', include('api.Users.urls')),
]