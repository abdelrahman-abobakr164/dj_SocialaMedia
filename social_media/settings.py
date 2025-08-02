import os
from pathlib import Path
from environ import Env

env = Env()
Env.read_env()
ENVIRONMENT = env("ENVIRONMENT")
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/5.1/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = env("SECRET_KEY")

STRIPE_PUBLISHABLE_KEY = "pk_test_51Q3xnYH4IAM7G10vw0mAzfEqkajCpWH5PuIrYJziEdvBURYUnHzQXitK8ntYVdqoGknPH0fw9p8cHoErROxU1eGu00xRPC5XiA"
STRIPE_SECRET_KEY = "sk_test_51Q3xnYH4IAM7G10vjZxB1hYy3pSjbEypfl8OkJh7j6AbDCMw4fLXPiTp1t1A6Yh8CfGDK1gXZMudT4m0wcOqTET200aouCIE60"

# SECURITY WARNING: don't run with debug turned on in production!
if ENVIRONMENT == "development":
    DEBUG = True
else:
    DEBUG = False

ALLOWED_HOSTS = ["127.0.0.1", "localhost", "eager-badly-crayfish.ngrok-free.app"]

CSRF_TRUSTED_ORIGINS = ["https://eager-badly-crayfish.ngrok-free.app"]

INSTALLED_APPS = [
    "daphne",
    "jazzmin",
    "channels",
    "accounts",
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "core",
    "notifications",
    "conversation",
    "story",
    "allauth",
    "allauth.account",
    "allauth.socialaccount",
    "allauth.socialaccount.providers.google",
    "django.contrib.sitemaps",
    "django_bootstrap5",
    "django_social_share",
    "debug_toolbar",
]

# Jazzmin Settings
JAZZMIN_SETTINGS = {
    "site_title": "Social Media Admin",
    "site_header": "Social Media",
    "site_brand": "Social Media",
    "site_logo": "/images/favicon.png",
    "welcome_sign": "Welcome to the Social Media Admin",
    "copyright": "Social Media",
    "search_model": ["accounts.User"],
    "user_avatar": None,
}

ASGI_APPLICATION = "social_media.asgi.application"

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.middleware.locale.LocaleMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "allauth.account.middleware.AccountMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
]

ROOT_URLCONF = "social_media.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": ["templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
                "accounts.context_processors.follow_suggestions",
                "core.context_processors.content_types",
                "conversation.context_processors.conversations_count",
                "story.context_processors.user_stories",
            ],
        },
    },
]

ASGI_APPLICATION = "social_media.asgi.application"
WSGI_APPLICATION = "social_media.wsgi.application"


SOCIALACCOUNT_PROVIDERS = {
    "google": {
        "SCOPE": [
            "profile",
            "email",
        ],
        "AUTH_PARAMS": {
            "access_type": "online",
            "prompt": "select_account",
        },
    }
}


AUTH_USER_MODEL = "accounts.user"


# Database
# https://docs.djangoproject.com/en/5.1/ref/settings/#databases

DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.sqlite3",
        "NAME": BASE_DIR / "db.sqlite3",
    }
}

# DATABASES = {
#     "default": {
#         "ENGINE": "django.db.backends.postgresql",
#         "NAME": env("DB_NAME"),
#         "USER": env("DB_USER"),
#         "PASSWORD": env("DB_PASSWORD"),
#         "HOST": env("DB_HOST"),
#         "PORT": env("DB_PORT"),
#     }
# }


SITE_ID = 1


# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation.UserAttributeSimilarityValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.MinimumLengthValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.CommonPasswordValidator",
    },
    {
        "NAME": "django.contrib.auth.password_validation.NumericPasswordValidator",
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "Africa/Cairo"


USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = "/static/"
STATIC_ROOT = BASE_DIR / "staticfiles"
STATICFILES_DIRS = [BASE_DIR / "static"]  # R
STATICFILES_STORAGE = "whitenoise.storage.CompressedManifestStaticFilesStorage"

MEDIA_URL = "/media/"  # R
MEDIA_ROOT = os.path.join(BASE_DIR, "media")  # R

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Logging Configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'websocket_debug.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'conversation.consumers': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': False,
        },
        'django.channels': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
    },
}

# Channel Layers Configuration for WebSocket
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": (
            "channels.layers.InMemoryChannelLayer"
            if DEBUG
            else "channels_redis.core.RedisChannelLayer"
        ),
        "CONFIG": {} if DEBUG else {"hosts": [("127.0.0.1", 6379)]},
    },
}

AUTHENTICATION_BACKENDS = [
    "django.contrib.auth.backends.ModelBackend",
    "allauth.account.auth_backends.AuthenticationBackend",
]
LOGIN_REDIRECT_URL = "/"
LOGOUT_REDIRECT_URL = "/"

# Email
ACCOUNT_SIGNUP_FIELDS = ["email*", "username*", "password1*", "password2*"]
ACCOUNT_CHANGE_EMAIL = True
ACCOUNT_EMAIL_CHANGE_REQUEST = True
ACCOUNT_LOGIN_METHODS = {"email"}
ACCOUNT_CONFIRM_EMAIL_ON_GET = True
ACCOUNT_EMAIL_NOTIFICATIONS = True
ACCOUNT_EMAIL_VERIFICATION = "mandatory"
ACCOUNT_EMAIL_CONFIRMATION_AUTHENTICATED_REDIRECT_URL = "/accounts/login/"
ACCOUNT_LOGOUT_REDIRECT_URL = "/"
ACCOUNT_USERNAME_BLACKLIST = [
    "admin",
    "boda",
    "administrator",
    "moderator",
    "staff",
    "superuser",
    "support",
    "help",
    "root",
]

EMAIL_BACKEND = "django.core.mail.backends.console.EmailBackend"
EMAIL_HOST = "smtp.gmail.com"
EMAIL_PORT = 587
EMAIL_USE_TLS = True
EMAIL_HOST_USER = env("EMAIL_HOST_USER")
EMAIL_HOST_PASSWORD = env("EMAIL_HOST_PASSWORD")
DEFAULT_FROM_EMAIL = f'Sociala {env("EMAIL_HOST_USER")}'
ACCOUNT_EMAIL_SUBJECT_PREFIX = ""
