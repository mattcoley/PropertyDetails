from django.urls import path
from . import property_details

urlpatterns = [
    path('property/details', property_details.property_details, name="property_details"),
]
