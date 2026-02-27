from django.shortcuts import render
from rest_framework.response import Response
from rest_framework import status, viewsets, filters
from rest_framework.decorators import action
from django.core.exceptions import MultipleObjectsReturned
from django.db.utils import IntegrityError
from .models import Products, Sizes, Colors, ProductPhoto, VariantProduct
from .serializers import ProductsSerializer, PatchStateProductsSerializer, ColorsSerializer, SizesSerializer, ProductsPhotosSerializer, VariantProductsSerializer
from django.shortcuts import get_list_or_404,get_object_or_404
from .services import create_inventory_for_variant
from django.db import transaction

class ProductsViewSets(viewsets.GenericViewSet):
    queryset = Products.objects.all()
    serializer_class = ProductsSerializer
    # authentication_classes = []
    # permission_classes = []
    filter_backends = [filters.SearchFilter]
    search_fields = ['id_product','name','category','price','is_active']

    def get_serializer_class(self):
        if self.action == 'partial_update':
            return PatchStateProductsSerializer
        return ProductsSerializer
    
    @action(detail=False,methods=['GET'])
    def get_products(self, request):
        try:
            products = self.get_queryset()
            serializer = self.get_serializer(products, many=True)
            return Response({'message':'productos obtenidos', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True,methods=['GET'])
    def get_products_by_id(self, request, pk=None):
        try:
            product = self.get_object()
            serialzier = self.get_serializer(product, many=False)
            return Response({'message':'producto encontrado', 'results':serialzier.data, 'success':True}, status=status.HTTP_200_OK)
        except Products.DoesNotExist:
            return Response({'message':'producto no encontrada', 'results':[], 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'resutls':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False,methods=['POST'])
    def create_products(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'creado exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message':'error de lalves', 'results':[], 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_products(self, request, pk=None):
        try:
            product = self.get_object()
            product.delete()
            return Response({'message':'elimiando exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_products(self, request, pk=None):
        try:
            product = self.get_object()
            serializer = self.get_serializer(product, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'actualizado exitosamente', 'product':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Products.DoesNotExist:
            return Response({'message':'este producto no existe', 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False,methods=['GET'])
    def search_products(self, request):
        try:
            queryset = self.get_queryset()
            instance = self.filter_queryset(queryset=queryset)
            serializer = self.get_serializer_class(instance, many=True)
            return Response({'message':'productos encontrados', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Products.DoesNotExist:
            return Response({'message':'no se encontraron productos', 'results':[], 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PATCH'])
    def patch_state(self, request, pk=None):
        try:
            product = self.get_object()
            serializer = self.get_serializer_class(product, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'estado actualizado exitosamente', 'product':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Products.DoesNotExist:
            return Response({'message':'este producto no existe', 'results':[], 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except IntegrityError:
            return Response({'message':'error de llaves', 'results':[], 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ColorViewSets(viewsets.GenericViewSet):
    queryset = Colors.objects.all()
    serializer_class = ColorsSerializer
    # permission_classes = []
    # authentication_classes = []

    @action(detail=False,methods=['GET'])
    def get_colors(self, request):
        try:
            colors = self.get_queryset()
            serializer = self.get_serializer(colors,many=True)
            return Response({'message':'colores obtenidos exitosamente', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_colors_by_id(self, request, pk=None):
        try:
            color = self.get_object()
            serializer = self.get_serializer(color,many=False)
            return Response({'message':'color obtenido','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','results':[],'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_colors(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'color creado exitosamente','object':serializer.data,'success':True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message':'error de llaves','success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_color(self, request, pk=None):
        try:
            color = self.get_object()
            color.delete()
            return Response({'message':'eliminado exitosamente','success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Colors.DoesNotExist:
            return Response({'message':'este color no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex),'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_color(self, request, pk=None):
        try:
            color = self.get_object()
            serializer = self.get_serializer(color, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'color actualizado exitosamente', 'color':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetso retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Colors.DoesNotExist:
            return Response({'message':'este color no existe','success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class SizesViewSets(viewsets.GenericViewSet):
    queryset = Sizes.objects.all()
    serializer_class = SizesSerializer
    # permission_classes = []
    # authentication_classes = []

    @action(detail=False,methods=['GET'])
    def get_sizes(self, request):
        try:
            sizes = self.get_queryset()
            serializer = self.get_serializer(sizes, many=True)
            return Response({'message':'tallas obtenidas', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_sizes_by_id(self, request, pk=None):
        try:
            size = self.get_object()
            serializer = self.get_serializer(size,many=False)
            return Response({'message':'talla obtenida', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return  Response({'message':'multiples objetos retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_sizes(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'talla creada exitosamente', 'object':serializer.data, 'success':True}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message':'error de llaves', 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_sizes(self, request, pk=None):
        try:
            size = self.get_object()
            size.delete()
            return Response({'message':'eliminado exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'results':[], 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Sizes.DoesNotExist:
            return Response({'message':'esta talla no existe', 'results':[], 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['PUT'])
    def update_sizes(self, request, pk=None):
        try:
            size = self.get_object()
            serializer = self.get_serializer(size, data=request.data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'talla actualizada exitosamente','size':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Sizes.DoesNotExist:
            return Response({'message':'esta talla no existe', 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        

class ProductPhotosViewSets(viewsets.GenericViewSet):
    queryset = ProductPhoto.objects.all()
    serializer_class = ProductsPhotosSerializer
    # permission_classes = []
    # authentication_classes = []

    @action(detail=False,methods=['GET'])
    def get_photos(self, request):
        try:
            photos = self.get_queryset()
            serializer = self.get_serializer(photos,many=False)
            return Response({'message':'fotos obtenidas', 'results':serializer.data, 'success':True}, status=status.HTTP_200_OK)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['GET'])
    def get_photos_by_id(self, request, pk=None):
        try:
            photo = self.get_object()
            serializer = self.get_serializer(photo,many=False)
            return Response({'message':'foto obtenida', 'results':serializer.data, 'success':False}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])
    def create_photos(self, request):
        try:
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'message':'photo agregada exitosamente', 'object':serializer.data, 'success':False}, status=status.HTTP_201_CREATED)
        except IntegrityError:
            return Response({'message':'error de llaves', 'success':False}, status=status.HTTP_400_BAD_REQUEST)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=True,methods=['DELETE'])
    def delete_photos(self, request, pk=None):
        try:
            photo = self.get_object()
            photo.delete()
            return Response({'message':'foto eliminada exitosamente', 'success':False}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        except ProductPhoto.DoesNotExist:
            return Response({'message':'esta foto no existe', 'success':False}, status=status.HTTP_404_NOT_FOUND)
        except Exception as ex:
            return Response({'error':str(ex), 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
class VariantProductViewSets(viewsets.GenericViewSet):
    queryset = VariantProduct.objects.all()
    serializer_class = VariantProductsSerializer    
    # permission_classes = []
    # authentication_classes = []

    @action(detail=False,methods=['GET'])
    def get_variants(self, request):
            variants = self.get_queryset()
            serializer = self.get_serializer(variants,many=True)
            return Response({'message':'variantes obtenidas exitosamente','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
    
    @action(detail=True,methods=['GET'])
    def get_variants_by_id(self, request, pk=None):
        try:
            variant = self.get_object()
            serializer = self.get_serializer(variant,many=False)
            return Response({'message':'variante obtenida','results':serializer.data,'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados','results':[],'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
    @action(detail=False,methods=['POST'])    
    def create_variant(self, request):
        with transaction.atomic():
            data = request.data
            serializer = self.get_serializer(data=data)
            serializer.is_valid(raise_exception=True)
            variant = serializer.save()

            create_inventory_for_variant(variant=variant)
            return Response({'message':'variante creada exitosamente', 'object':serializer.data,'success':True},status=status.HTTP_201_CREATED)
        
    @action(detail=True,methods=['DELETE'])
    def delete_variant(self, request, pk=None):
        try:
            variant = self.get_object()
            variant.delete()
            return Response({'message':'variante eliminada exitosamente', 'success':True}, status=status.HTTP_200_OK)
        except MultipleObjectsReturned:
            return Response({'message':'multiples objetos retornados', 'success':False}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
        
        
    
        



        
        
# Create your views here.
