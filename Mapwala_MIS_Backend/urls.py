# Mapwala_MIS_Backend/urls.py
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.generic import RedirectView


def health_check(request):
    return JsonResponse({"status": "ok", "service": "Mapwala MIS API"}, status=200)


urlpatterns = [
    path("", health_check, name="health-check"),
    path("admin/dashboard/", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", include("mapwala_mis.urls")),
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
