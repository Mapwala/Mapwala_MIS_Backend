from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import *

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
    
    path("devices/step-1/", DeviceStep1APIView.as_view()),
    path("devices/step-2/", DeviceStep2APIView.as_view()),
    path("devices/step-3/", DeviceStep3APIView.as_view()),
    path("devices/step-4/", DeviceStep4APIView.as_view()),
    path("devices/step-5/", DeviceStep5APIView.as_view()),
    path("devices/step-6/", DeviceStep6APIView.as_view()),
    path("devices/step-7/", DeviceStep7APIView.as_view()),
    path("devices/step-8/", DeviceStep8APIView.as_view()),
    path("devices/step-9/", DeviceStep9APIView.as_view()),
    path("devices/step-10/", DeviceAccessoryAPIView.as_view()),
    
    path("pi/create/", ProformaInvoiceCreateAPIView.as_view(), name="create-pi"),
]

urlpatterns += router.urls
