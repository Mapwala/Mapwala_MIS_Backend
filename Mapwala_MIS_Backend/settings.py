from pathlib import Path
import os
from dotenv import load_dotenv
import dj_database_url
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
ALLOWED_HOSTS = os.getenv("ALLOWED_HOSTS", "localhost").split(",")


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
CORS_ALLOWED_ORIGINS = os.getenv("CORS_ALLOWED_ORIGINS", "http://localhost:3000").split(",")

ROOT_URLCONF = "Mapwala_MIS_Backend.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [],
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


# Database
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    DB_ENGINE = os.getenv("DB_ENGINE", "postgresql")
    DB_NAME = os.getenv("DB_NAME")
    DB_USER = os.getenv("DB_USER")
    DB_PASSWORD = os.getenv("DB_PASSWORD")
    DB_HOST = os.getenv("DB_HOST", "localhost")
    DB_PORT = os.getenv("DB_PORT", "5432")

    if not all([DB_NAME, DB_USER, DB_PASSWORD]):
        raise RuntimeError("Database environment variables are not fully set")

    DATABASE_URL = f"{DB_ENGINE}://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

DATABASES = {
    "default": dj_database_url.parse(
        DATABASE_URL,
        conn_max_age=600,
    )
}


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

# Jazzmin Configuration
JAZZMIN_SETTINGS = {
    # Window title
    "site_title": "Mapwala MIS Admin",
    # Header text
    "site_header": "Mapwala MIS",
    # Brand text (top left)
    "site_brand": "Mapwala MIS",
    # Logo (optional — keep None unless you add a static logo)
    "site_logo": None,
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    # Favicon
    "site_icon": None,
    # Login welcome
    "welcome_sign": "Welcome to Mapwala MIS",
    # Footer text
    "copyright": "© Mapwala Technologies",
    # Search models
    "search_model": ["auth.User", "auth.Group"],
    # Avatar field
    "user_avatar": None,
    ################
    # Top Menu
    ################
    "topmenu_links": [
        {"name": "Home", "url": "admin:index"},
        {"model": "auth.User"},
        {"model": "auth.Group"},
    ],
    ################
    # User Menu
    ################
    "usermenu_links": [
        {"name": "Support", "url": "https://mapwala.com", "new_window": True},
    ],
    ################
    # Side Menu
    ################
    "show_sidebar": True,
    "navigation_expanded": False,
    "hide_apps": [],
    "hide_models": [],
    # Order side menu
    "order_with_respect_to": ["auth", "mapwala_mis"],
    ################
    # Icons
    ################
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",
        "mapwala_mis": "fas fa-database",
    },
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    ################
    # UI Tweaks
    ################
    "related_modal_active": False,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    ################
    # Change Form
    ################
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.user": "collapsible",
        "auth.group": "vertical_tabs",
    },
    "language_chooser": False,
    
    "icons": {
        "auth": "fas fa-users-cog",
        "auth.user": "fas fa-user",
        "auth.group": "fas fa-users",

        "mapwala_mis": "fas fa-database",
        "mapwala_mis.state": "fas fa-map",
        "mapwala_mis.district": "fas fa-map-marked-alt",
        "mapwala_mis.parentcompany": "fas fa-building",
        "mapwala_mis.vendor": "fas fa-truck",
        "mapwala_mis.b2ccustomer": "fas fa-user-tag",
        "mapwala_mis.b2bpartner": "fas fa-handshake",
        "mapwala_mis.userprofile": "fas fa-id-badge",
    },
    
    "search_model": [
        "auth.User",
        "auth.Group",
        "mapwala_mis.ParentCompany",
        "mapwala_mis.Vendor",
        "mapwala_mis.B2CCustomer",
        "mapwala_mis.B2BPartner",
    ],
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

