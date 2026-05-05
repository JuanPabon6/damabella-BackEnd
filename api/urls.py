from django.urls import path,include

urlpatterns = [
    path('', include('api.Roles.urls')),
    path('', include('api.Users.urls')),
    path('', include('api.Providers.urls')),
    path('', include('api.Categories.urls')),
    path('', include('api.Products.urls')),
    path('', include('api.Inventory.urls')),
    path('', include('api.Clients.urls')),
    path('', include('api.Purchases.urls')),
    path('', include('api.States.urls')),
    path('', include('api.Orders.urls')),
    path('', include('api.Sales.urls')),
]