from django.urls import path,include

urlpatterns = [
    path('', include('api.Roles.urls')),
    path('', include('api.Users.urls')),
    path('', include('api.Providers.urls'))
]