import os

from django.core.wsgi import get_wsgi_application

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "Mapwala_MIS_Backend.settings")

application = get_wsgi_application()
