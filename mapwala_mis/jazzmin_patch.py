from django.utils.html import format_html as django_format_html
from django.utils.safestring import mark_safe


def safe_format_html(format_string, *args, **kwargs):
    if not args and not kwargs:
        return mark_safe(format_string)
    return django_format_html(format_string, *args, **kwargs)
