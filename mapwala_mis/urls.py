from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import (LoginAPIView,StateViewSet,DistrictViewSet,ParentCompanyViewSet,VendorViewSet,B2CCustomerRegistrationAPIView,B2BPartnerRegistrationAPIView,DistributorRegistrationAPIView,DealerRegistrationAPIView, ProformaInvoiceCreateAPIView)

router = DefaultRouter()
router.register("states", StateViewSet, basename="states")
router.register("districts", DistrictViewSet, basename="districts")
router.register("parent-companies", ParentCompanyViewSet, basename="parent-companies")
router.register("vendors", VendorViewSet, basename="vendors")

urlpatterns = [
    path("auth/login/", LoginAPIView.as_view(), name="login"),
    path("b2c/register/", B2CCustomerRegistrationAPIView.as_view(), name="b2c-register"),
    path("b2b/register/", B2BPartnerRegistrationAPIView.as_view(), name="b2b-register"),
    path("distributor/register/", DistributorRegistrationAPIView.as_view(), name="distributor-register"),
    path("dealer/register/",DealerRegistrationAPIView.as_view(),name="dealer-register"),
    path("pi/create/", ProformaInvoiceCreateAPIView.as_view(), name="create-pi"),
]

urlpatterns += router.urls
