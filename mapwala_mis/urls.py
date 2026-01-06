from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LoginAPIView, StateViewSet, DistrictViewSet, ParentCompanyViewSet, VendorViewSet

router = DefaultRouter()
router.register("states", StateViewSet, basename="states")
router.register("districts", DistrictViewSet, basename="districts")
router.register("parent-companies", ParentCompanyViewSet, basename="parent-companies")
router.register("vendors", VendorViewSet, basename="vendors")

urlpatterns = [
    path("auth/login/", LoginAPIView.as_view(), name="login"),
]

urlpatterns += router.urls
