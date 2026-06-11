from django.shortcuts import render
from rest_framework import viewsets
from rest_framework import (generics,permissions,renderers,)

from commoninfo.permissions import IsOwnerOrReadOnly,CustomDjangoModelPermissions
from .models import (StgResourceType, StgKnowledgeProduct, StgProductDomain,)
from publications.serializers import (StgResourceTypeSerializer,
    StgKnowledgeProductSerializer,StgKnowledgeDomainSerializer,)

from admin_auto_filters.views import AutocompleteJsonView #added on 02/02/2023


class StgResourceTypeViewSet(viewsets.ModelViewSet):
    serializer_class = StgResourceTypeSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgResourceType.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()



class StgKnowledgeDomainViewSet(viewsets.ModelViewSet):
    serializer_class = StgKnowledgeDomainSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgProductDomain.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()



class StgKnowledgeProductViewSet(viewsets.ModelViewSet):
    serializer_class = StgKnowledgeProductSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,IsOwnerOrReadOnly)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        queryset =  StgKnowledgeProduct.objects.filter(
                    translations__language_code=language).order_by(
                    'translations__title').distinct()
        user = self.request.user.id
        groups = list(self.request.user.groups.values_list('user', flat=True))
        location = self.request.user.location_id
        if self.request.user.is_superuser:
            qs=queryset
        elif user in groups: # Match fact location field to that of logged user
            qs=queryset.filter(location=location)
        else:
            qs=queryset.filter(user=user)
        return qs


class KnowledgeResourceSearchView(AutocompleteJsonView):
    model_admin = None # this view controls display of loacations 
    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        user = self.request.user.id
        groups = list(self.request.user.groups.values_list('user', flat=True))
        location = self.request.user.location_id

        queryset = StgResourceType.objects.prefetch_related(
            'translations').filter(translations__language_code=language).distinct()
        if self.request.user.is_superuser:
            qs = queryset.order_by( # return all locations ordered by level then name
                'translations__name') 
        elif user in groups: # Match fact location field to that of logged user
            qs = queryset.filter(locationlevel__lte=2).order_by(
                'translations__name') # return AFRO countries only
        else:
            qs = queryset.filter(location=location).order_by(
                'translations__name') # return the data for user's country
        return qs
