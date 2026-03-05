from rest_framework.permissions import BasePermission
from api.Roles.models import RolPermission

class HasModulePermission(BasePermission):
    message = "no tienes permisos para realizar esta accion"

    Actions_map = {
        #Categories
        'create_categories' : 'Create',# 'Delete', 'View', 'Edit', 'Create
        'get_categories' : 'View',
        'search_categories' : 'View',
        'get_categories_by_id' : 'View',
        'delete_categories' : 'Delete',
        'update_categories' : 'Edit',

        #Clients
        'create_clients' : 'Create',
        'get_clients' : 'View',
        'search_clients' : 'View',
        'get_clients_by_id' : 'View',
        'delete_clients' : 'Delete',
        'update_clients' : 'Edit',

        #Products
        'create_products' : 'Create',
        'get_products' : 'View',
        'search_products' : 'View',
        'get_products_by_id' : 'View',
        'delete_products' : 'Delete',
        'update_products': 'Edit',

        #Providers
        'create_providers' :  'Create',
        'get_providers' : 'View',
        'search_providers' : 'View',
        'get_providers_by_id' : 'View',
        'delete_providers' : 'Delete',
        'update_providers' : 'Edit',

        #Roles
        'create_roles' : 'Create',
        'get_roles' : 'View',
        'search_roles' : 'View',
        'get_rol_by_id' : 'View',
        'export_users' : 'View',
        'delete_rol' : 'Delete',
        'update_roles' : 'Edit',

        #compartidos
        'change_state' : 'Edit',
        'patch_state' : 'Edit',
    }

    def has_permission(self, request, view):
        print('USER:', request.user)
        print('IS AUTHENTICATED:', request.user.is_authenticated)
        print('AUTH:', request.auth)
        print('MODULE:', getattr(view, 'required_module', None))
        print('ACTION:', getattr(view, 'action', None))
        if not request.user or not request.user.is_authenticated:
            return False
        
        module = getattr(view, 'required_module', None)
        if not module:
            return True

        action = self.Actions_map.get(view.action, 'View')
        return RolPermission.objects.filter(
            rol= request.user.id_rol,
            permission__Module_permission=module,
            permission__Action=action
        ).exists()