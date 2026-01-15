from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import RedirectView

def home(request):
    return HttpResponse("<h1>Django is running</h1><strong><p>Use /admin or /api</p></strong>")

urlpatterns = [
    path("", home, name="home"),
    path("admin/dashboard/", RedirectView.as_view(url="/admin/", permanent=False)),
    path("admin/", admin.site.urls),
    path("api/", include("mapwala_mis.urls")), 
]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)