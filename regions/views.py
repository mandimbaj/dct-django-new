from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import (generics,permissions,renderers,)

from admin_auto_filters.views import AutocompleteJsonView #added on 02/02/2023

from commoninfo.permissions import IsOwnerOrReadOnly,CustomDjangoModelPermissions
from .models import (StgWorldbankIncomegroups,StgLocationLevel,
    StgEconomicZones, StgLocation)
from regions.serializers import (StgLocationLevelSerializer,
    StgEconomicZonesSerializer,StgWorldbankIncomegroupsSerializer,
    StgLocationSerializer,)

class StgLocationLevelViewSet(viewsets.ModelViewSet):
    serializer_class = StgLocationLevelSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgLocationLevel.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()



class StgEconomicZonesViewSet(viewsets.ModelViewSet):
    serializer_class = StgEconomicZonesSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgEconomicZones.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgWorldbankIncomegroupsViewSet(viewsets.ModelViewSet):
    serializer_class = StgWorldbankIncomegroupsSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgWorldbankIncomegroups.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()



class StgLocationViewSet(viewsets.ModelViewSet):
    serializer_class = StgLocationSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgLocation.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class LocationSearchView(AutocompleteJsonView):
    model_admin = None # this view controls display of loacations 
    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        user = self.request.user.id
        groups = list(self.request.user.groups.values_list('user', flat=True))
        location = self.request.user.location_id

        queryset = StgLocation.objects.select_related(
            'locationlevel').prefetch_related('translations__master').filter(
            translations__language_code=language).distinct()
        if self.request.user.is_superuser:
            qs = queryset.order_by( # return all locations ordered by level then name
                'locationlevel','translations__name') 
        elif user in groups: # Match fact location field to that of logged user
            qs = queryset.filter(locationlevel__lte=2).order_by(
                'locationlevel','translations__name') # return AFRO countries only
        else:
            qs = queryset.filter(location=location).order_by(
                'locationlevel','translations__name') # return the data for user's country
        return qs