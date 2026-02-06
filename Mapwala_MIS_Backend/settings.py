from pathlib import Path
import os
from dotenv import load_dotenv
from datetime import timedelta

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

load_dotenv(BASE_DIR / ".env")

# SECURITY WARNING: keep the secret key used in production secret!
# SECRET_KEY = "django-insecure-$$r#&nv4_bt-^v2t)02-#o!yep^$i1c)m(k@59+mjhn^-aaog7"
SECRET_KEY = os.getenv("SECRET_KEY")
if not SECRET_KEY:
    raise RuntimeError("SECRET_KEY is not set in .env file")


# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv("DEBUG") == "True"

# ALLOWED_HOSTS = ["*"]
ALLOWED_HOSTS = [
    host.strip()
    for host in os.getenv("ALLOWED_HOSTS", "localhost").split(",")
    if host.strip()
]


# Application definition

INSTALLED_APPS = [
    "jazzmin",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "corsheaders",
    "rest_framework",
    "mapwala_mis",
]

MIDDLEWARE = [
    "corsheaders.middleware.CorsMiddleware",
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

# CORS SETTINGS
# Allow comma-separated origins in .env; tolerate spaces after commas.
CORS_ALLOWED_ORIGINS = [
    origin.strip()
    for origin in os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")
    if origin.strip()
]

ROOT_URLCONF = "Mapwala_MIS_Backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]


WSGI_APPLICATION = "Mapwala_MIS_Backend.wsgi.application"


# Database Configuration (NO DATABASE_URL)

_raw_db_engine = (os.getenv("DB_ENGINE") or "django.db.backends.postgresql").strip()
_db_engine_aliases = {
    # Common shorthands people put in .env
    "postgres": "django.db.backends.postgresql",
    "postgresql": "django.db.backends.postgresql",
    "sqlite": "django.db.backends.sqlite3",
    "sqlite3": "django.db.backends.sqlite3",
    "mysql": "django.db.backends.mysql",
    "oracle": "django.db.backends.oracle",
}
_db_engine = _db_engine_aliases.get(_raw_db_engine, _raw_db_engine)

DATABASES = {
    "default": {
        "ENGINE": _db_engine,
        "NAME": os.getenv("DB_NAME"),
        "USER": os.getenv("DB_USER"),
        "PASSWORD": os.getenv("DB_PASSWORD"),
        "HOST": os.getenv("DB_HOST", "localhost"),
        "PORT": os.getenv("DB_PORT", "5432"),
        "CONN_MAX_AGE": 600,
    }
}

# Safety Check (Recommended)
if not all(
    [
        DATABASES["default"]["NAME"],
        DATABASES["default"]["USER"],
        DATABASES["default"]["PASSWORD"],
    ]
):
    raise RuntimeError("❌ Database environment variables are not fully set")


# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.NumericPasswordValidator"},
]


# Internationalization
LANGUAGE_CODE = "en-us"
TIME_ZONE = "UTC"
USE_I18N = True
USE_TZ = True


# REST FRAMEWORK CONFIGURATION
REST_FRAMEWORK = {
    "DEFAULT_AUTHENTICATION_CLASSES": (
        "rest_framework_simplejwt.authentication.JWTAuthentication",
    ),
    "DEFAULT_PERMISSION_CLASSES": (
        "rest_framework.permissions.IsAuthenticated",
    ),
    "DEFAULT_THROTTLE_CLASSES": [
        "rest_framework.throttling.AnonRateThrottle",
        "rest_framework.throttling.UserRateThrottle",
    ],
    "DEFAULT_THROTTLE_RATES": {
        "anon": "100/day",
        "user": "1000/hour",
        "login": "5/min",
    },
    "DEFAULT_PAGINATION_CLASS": "rest_framework.pagination.PageNumberPagination",
    "PAGE_SIZE": 50,
}

# Simple JWT Configuration
SIMPLE_JWT = {
    "ACCESS_TOKEN_LIFETIME": timedelta(hours=24),
    "REFRESH_TOKEN_LIFETIME": timedelta(seconds=0),
    "AUTH_HEADER_TYPES": ("Bearer",),
}

# ==================== Jazzmin Core Settings ====================
JAZZMIN_SETTINGS = {
    # -------------------- General --------------------
    "site_title": "Mapwala MIS Admin",
    "site_header": "Mapwala MIS",
    "site_brand": "Mapwala MIS",
    "welcome_sign": "Welcome to Mapwala MIS",
    "copyright": "© Mapwala Technologies",

    # -------------------- Logos --------------------
    "site_logo": None,
    "site_logo_classes": "img-circle",
    "site_icon": "fas fa-warehouse",
    "login_logo": None,
    "login_logo_dark": None,

    # -------------------- Theme --------------------
    "theme": "flatly",
    "dark_mode_theme": None,
    "show_theme_switcher": True,

    # -------------------- Layout --------------------
    "show_sidebar": True,
    "navigation_expanded": False,
    "order_with_respect_to": ["auth", "mapwala_mis"],

    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },

    # -------------------- Sidebar --------------------
    "sidebar_fixed": True,
    "sidebar": {
        "scrollbar_theme": "os-theme-dark",
        "scrollbar_auto_hide": "l",
    },

    # -------------------- Icons --------------------
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user-circle",
        "auth.group": "fas fa-users",

        "mapwala_mis": "fas fa-database",
        "mapwala_mis.state": "fas fa-map",
        "mapwala_mis.district": "fas fa-map-marked-alt",
        "mapwala_mis.parentcompany": "fas fa-building",
        "mapwala_mis.vendor": "fas fa-truck-loading",
        "mapwala_mis.b2ccustomer": "fas fa-user-tag",
        "mapwala_mis.b2bpartner": "fas fa-handshake",
        "mapwala_mis.userprofile": "fas fa-id-card",

        "admin.LogEntry": "fas fa-history",
        "sessions": "fas fa-clock",
        "sites": "fas fa-globe",
    },

    "default_icon_parents": "fas fa-chevron-right",
    "default_icon_children": "fas fa-circle",

    # -------------------- Menus --------------------
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "Dashboard", "url": "/admin/dashboard/"},
        {"model": "auth.User"},
        {"model": "auth.Group"},
        {"name": "Support", "url": "https://mapwala.com/support", "new_window": True, "icon": "fas fa-life-ring"},
    ],

    "usermenu_links": [
        {
            "name": "Profile",
            "url": "admin:auth_user_change",
            "icon": "fas fa-user-edit",
            "url_args": lambda request: {"object_id": request.user.pk},
        },
        {"name": "Support", "url": "https://mapwala.com/support", "new_window": True, "icon": "fas fa-question-circle"},
        {"name": "Documentation", "url": "https://docs.mapwala.com", "new_window": True, "icon": "fas fa-book"},
        {"model": "auth.user"},
    ],

    # -------------------- UI Behaviour --------------------
    "related_modal_active": True,
    "use_google_fonts_cdn": True,
    "show_ui_builder": True,
    "actions_sticky_top": False,  # overridden by your tweak request
    "language_chooser": False,
    "collapse_nav": True,

    "form_nav_classes": {
        "default": "nav-tabs nav-justified",
        "auth.user": "nav-tabs",
    },
}

# ==================== Jazzmin UI Tweaks ====================
JAZZMIN_UI_TWEAKS = {
    # -------------------- Text sizes --------------------
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": True,
    "brand_small_text": False,

    # -------------------- Brand --------------------
    "brand_colour": False,

    # -------------------- Accent --------------------
    "accent": "accent-primary",

    # -------------------- Navbar --------------------
    "navbar": "navbar-dark",
    "navbar_dark": True,
    "navbar_color": "dark",
    "no_navbar_border": False,
    "navbar_fixed": False,

    # -------------------- Layout --------------------
    "layout_boxed": False,
    "footer_fixed": True,
    "sidebar_fixed": True,

    # -------------------- Sidebar --------------------
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": True,
    "sidebar_nav_compact_style": True,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": True,

    # -------------------- Theme --------------------
    "theme": "flatly",
    "dark_mode_theme": None,

    # -------------------- Buttons --------------------
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success",
    },

    # -------------------- Alerts --------------------
    "alert_classes": {
        "error": "alert-danger",
        "warning": "alert-warning",
        "success": "alert-success",
        "info": "alert-info",
    },

    # -------------------- Cards --------------------
    "card": {
        "theme": "dark",
        "background": "bg-dark",
        "border": "border-dark",
    },

    # -------------------- Tables --------------------
    "table": {
        "theme": "dark",
        "striped": True,
        "hover": True,
        "bordered": False,
        "condensed": True,
    },

    # -------------------- Forms --------------------
    "form": {
        "field_background": "bg-dark",
        "field_border": "border-secondary",
        "field_text_color": "text-light",
    },

    # -------------------- Modals --------------------
    "modal": {
        "theme": "dark",
        "backdrop": True,
    },

    # -------------------- Actions --------------------
    "actions_sticky_top": False,
}


# STATIC FILES
STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

# MEDIA FILES (for uploads like GST docs)
MEDIA_URL = "/media/"
MEDIA_ROOT = BASE_DIR / "media"

# Upload limits (security)
DATA_UPLOAD_MAX_MEMORY_SIZE = 5242880  # 5 MB
FILE_UPLOAD_MAX_MEMORY_SIZE = 5242880   # 5 MB
