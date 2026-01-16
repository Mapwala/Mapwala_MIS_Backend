from django.apps import AppConfig


class MapwalaMisConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "mapwala_mis"

    def ready(self):
        import jazzmin.templatetags.jazzmin
        from .jazzmin_patch import safe_format_html

        jazzmin.templatetags.jazzmin.format_html = safe_format_html
