# mapwala_mis/urls.py

from django.urls import path
from rest_framework.routers import DefaultRouter

from .views import LoginAPIView, StateViewSet, DistrictViewSet

router = DefaultRouter()
router.register("states", StateViewSet, basename="states")
router.register("districts", DistrictViewSet, basename="districts")

urlpatterns = [
    path("auth/login/", LoginAPIView.as_view(), name="login"),
]

urlpatterns += router.urls
