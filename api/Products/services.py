from api.Inventory.models import Inventory

def create_inventory_for_variant(variant):
    return Inventory.objects.create(
        variant = variant,
        stock = 0
    )