from django.shortcuts import render
<<<<<<< HEAD

=======
from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from .models import Sales, SalesDetail
from .serializers import SalesSerializer, SalesDetailsSerializer
from django.db.utils import IntegrityError
from django.core.exceptions import MultipleObjectsReturned
from api.Inventory.services import add_stock
from .services import Export_sales_list
import logging
from django.db import transaction
>>>>>>> juanjo
# Create your views here.
