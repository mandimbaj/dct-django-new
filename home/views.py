from django.shortcuts import render
from django.http import HttpResponseRedirect,HttpResponse
from django.contrib.auth import authenticate, login, logout
from django.shortcuts import redirect
from rest_framework import viewsets
from rest_framework import (generics,permissions,renderers,)
from rest_framework.decorators import api_view # new
from rest_framework.response import Response # new
from rest_framework.reverse import reverse # new

from admin_auto_filters.views import AutocompleteJsonView #added on 02/02/2023

from commoninfo.permissions import IsOwnerOrReadOnly,CustomDjangoModelPermissions
from . serializers import (StgDatasourceSerializer,
    StgDisagregationOptionsSerializer,StgDisagregationCategorySerializer,
    StgValueDatatypeSerializer,StgMeasuremethodSerializer,)
from .models import (StgDatasource,StgCategoryParent, StgCategoryoption,
    StgValueDatatype,StgMeasuremethod,)
from django.conf import settings
#Facilitate single sign on into Microsoft Azure AD
from authentication.auth.auth_decorators import microsoft_login_required

class StgDisagregationCategoryViewSet(viewsets.ModelViewSet):
    serializer_class = StgDisagregationCategorySerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgCategoryParent.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()

class StgDisagregationOptionsViewSet(viewsets.ModelViewSet):
    serializer_class = StgDisagregationOptionsSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgCategoryoption.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgDatasourceViewSet(viewsets.ModelViewSet):
    queryset = StgDatasource.objects.all()
    serializer_class = StgDatasourceSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgDatasource.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgValueDatatypeViewSet(viewsets.ModelViewSet):
    serializer_class = StgValueDatatypeSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgValueDatatype.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()


class StgMeasuremethodViewSet(viewsets.ModelViewSet):
    serializer_class = StgMeasuremethodSerializer
    permission_classes = (permissions.IsAuthenticated,
        CustomDjangoModelPermissions,)

    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        return StgMeasuremethod.objects.filter(
            translations__language_code=language).order_by(
            'translations__name').distinct()

class DataourceSearchView(AutocompleteJsonView):
    model_admin = None # this view controls display of loacations 
    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        user = self.request.user.id
        groups = list(self.request.user.groups.values_list('user', flat=True))
        location = self.request.user.location_id

        queryset = StgDatasource.objects.filter(
            translations__language_code=language).distinct()
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



class CategoryOptionSearchView(AutocompleteJsonView):
    model_admin = None # this view controls display of loacations 
    def get_queryset(self):
        language = self.request.LANGUAGE_CODE # get the en, fr or pt from the request
        user = self.request.user.id
        groups = list(self.request.user.groups.values_list('user', flat=True))
        location = self.request.user.location_id

        queryset = StgCategoryoption.objects.select_related('category').filter(
            translations__language_code=language).distinct()
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


# #For testing OpenID=based authentication workflow
@microsoft_login_required()
def home(request):
    return HttpResponse("Logged in")

# If pages need to be restricted to certain groups of users.
@microsoft_login_required(groups=("invitee", "guest"))
def specific_group_access(request):
    return HttpResponse("You are accessing  DCT as Guest or Admin User")

# This is a test login view for use will SSO
def login(request):
    return render(request, 'login.html')
    # import pdb; pdb.set_trace()

def logout(request):
    return render(request,'logout.html')

# Methods for custom error handlers that serve htmls in templates/home/errors
def handler404(request, exception):
    context = {}
    response = render(request, "errors/404.html", context=context)
    response.status_code = 404
    return response

def handler500(request):
    context = {}
    response = render(request, "errors/500.html", context=context)
    response.status_code = 500
    return response
