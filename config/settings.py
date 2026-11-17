"""
Django settings for competitor monitoring system.
"""
import os
import certifi
from pathlib import Path
from dotenv import load_dotenv

# Fix SSL certificate verification on Windows
os.environ.setdefault('SSL_CERT_FILE', certifi.where())
os.environ.setdefault('REQUESTS_CA_BUNDLE', certifi.where())

# Load environment variables
load_dotenv()

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# SECURITY WARNING: don't run with debug turned on in production!
# Defaults to False so a missing .env value fails safe.
DEBUG = os.getenv('DEBUG', 'False').strip().lower() == 'true'

# SECURITY WARNING: keep the secret key used in production secret!
_DEV_FALLBACK_SECRET_KEY = 'django-insecure-dev-only-key-do-not-use-in-production'
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', '').strip()
_secret_key_is_weak = (
    len(SECRET_KEY) < 50
    or SECRET_KEY.startswith('django-insecure')
    or 'change-this' in SECRET_KEY
    or 'your-secret-key' in SECRET_KEY
)
if _secret_key_is_weak:
    if not DEBUG:
        from django.core.exceptions import ImproperlyConfigured
        raise ImproperlyConfigured(
            'DJANGO_SECRET_KEY must be set to a unique random value of at least 50 characters '
            'when DEBUG is False. Generate one with: '
            'python -c "from django.core.management.utils import get_random_secret_key; '
            'print(get_random_secret_key())"'
        )
    SECRET_KEY = SECRET_KEY or _DEV_FALLBACK_SECRET_KEY

# Auth tokens expire after this many days; users must log in again afterwards.
TOKEN_TTL_DAYS = int(os.getenv('TOKEN_TTL_DAYS', '14'))

# Firecrawl API Configuration
FIRECRAWL_API_KEY = os.getenv('FIRECRAWL_API_KEY', '')

# Apify API Configuration
APIFY_API_TOKEN = os.getenv('APIFY_API_TOKEN', '')
APIFY_COMPANY_ACTOR_ID = os.getenv('APIFY_COMPANY_ACTOR_ID', 'automation-lab~linkedin-company-scraper')
APIFY_JOBS_ACTOR_ID = os.getenv('APIFY_JOBS_ACTOR_ID', 'valig~linkedin-jobs-scraper')
APIFY_POSTS_ACTOR_ID = os.getenv('APIFY_POSTS_ACTOR_ID', 'harvestapi~linkedin-profile-posts')
APIFY_FB_POSTS_ACTOR_ID = os.getenv('APIFY_FB_POSTS_ACTOR_ID', 'parseforge~facebook-posts-scraper')
APIFY_FB_PAGE_ACTOR_ID = os.getenv('APIFY_FB_PAGE_ACTOR_ID', 'parseforge~facebook-pages-scraper')
APIFY_INSTAGRAM_ACTOR_ID = os.getenv('APIFY_INSTAGRAM_ACTOR_ID', 'apify~instagram-scraper')

# OpenRouter API Configuration (used by Agno agents)
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY', '')

# OpenAI API Configuration
OPENAI_API_KEY = os.getenv('OPENAI_API_KEY', '')

# ChromaDB HTTP Server Configuration
CHROMA_HOST = os.getenv('CHROMA_HOST', '127.0.0.1')
CHROMA_PORT = int(os.getenv('CHROMA_PORT', '8001'))

# RAG Configuration
RAG_TOP_K = int(os.getenv('RAG_TOP_K', '10'))
RAG_CACHE_TTL = int(os.getenv('RAG_CACHE_TTL', '7200'))  # seconds; 0 disables caching

# Maximum number of subpage links allowed per competitor
MAX_COMPETITOR_LINKS = int(os.getenv('MAX_COMPETITOR_LINKS', '500'))

# Django admin site: where it lives and who may reach it (see utils/admin_security.py).
# Anyone not on the allowlist gets a 404. Change ADMIN_URL to something non-obvious in production.
ADMIN_URL = os.getenv('ADMIN_URL', 'admin/').strip().lstrip('/')
if ADMIN_URL and not ADMIN_URL.endswith('/'):
    ADMIN_URL += '/'
ADMIN_ALLOWED_IPS = [ip for ip in os.getenv('ADMIN_ALLOWED_IPS', '127.0.0.1,::1').split(',') if ip.strip()]
ADMIN_TRUSTED_PROXY_COUNT = int(os.getenv('ADMIN_TRUSTED_PROXY_COUNT', '0'))

ALLOWED_HOSTS = [
    h.strip() for h in os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',') if h.strip()
]

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    
    # Third-party apps
    'rest_framework',
    'rest_framework.authtoken',
    'corsheaders',
    'django_celery_beat',
    'django_celery_results',
    
    # Local apps
    'apps.accounts',
    'apps.monitoring',
    'apps.scraping',
    'apps.rag',
    'apps.analytics',
    'apps.social_media',
    'apps.reports',
    'apps.dashboard',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'utils.admin_security.AdminIPAllowlistMiddleware',
    'corsheaders.middleware.CorsMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'config.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'config.wsgi.application'

# Database - PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.getenv('POSTGRES_DB', 'competitor_monitoring'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# Milvus Vector Database Configuration
MILVUS_CONFIG = {
    'HOST': os.getenv('MILVUS_HOST', 'localhost'),
    'PORT': os.getenv('MILVUS_PORT', '19530'),
    'COLLECTION_NAME': os.getenv('MILVUS_COLLECTION', 'competitor_data'),
    'DIMENSION': int(os.getenv('MILVUS_DIMENSION', '768')),
}

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Static files (CSS, JavaScript, Images)
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_DIRS = [BASE_DIR / 'static']

# Media files
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# CORS Settings
CORS_ALLOWED_ORIGINS = os.getenv(
    'CORS_ALLOWED_ORIGINS',
    'http://localhost:1500,http://127.0.0.1:1500'
).split(',')

CORS_ALLOW_CREDENTIALS = True

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'utils.authentication.ExpiringTokenAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50,
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
    ],
    'EXCEPTION_HANDLER': 'utils.exceptions.custom_exception_handler',
    # Only views that opt in with throttle_scope are throttled (login/register).
    'DEFAULT_THROTTLE_RATES': {
        'login': os.getenv('THROTTLE_LOGIN', '10/min'),
        'register': os.getenv('THROTTLE_REGISTER', '10/hour'),
    },
}

# The browsable API is a debugging aid; expose JSON only in production.
if not DEBUG:
    REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = ['rest_framework.renderers.JSONRenderer']

# Celery Configuration
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_BEAT_SCHEDULER = 'django_celery_beat.schedulers:DatabaseScheduler'

# Logging
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {message}',
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
            'filename': BASE_DIR / 'logs' / 'django.log',
            'formatter': 'verbose',
        },
    },
    'root': {
        'handlers': ['console', 'file'],
        'level': 'INFO',
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': os.getenv('DJANGO_LOG_LEVEL', 'INFO'),
            'propagate': False,
        },
    },
}

# Scripts Configuration
SCRIPTS_DIR = BASE_DIR / 'scripts'


# Cache — LocMemCache by default; switch to django-redis in production:
# pip install django-redis, then set CACHE_BACKEND=django_redis.cache.RedisCache
CACHES = {
    'default': {
        'BACKEND': os.getenv(
            'CACHE_BACKEND',
            'django.core.cache.backends.locmem.LocMemCache',
        ),
        'LOCATION': os.getenv('CACHE_LOCATION', 'redis://127.0.0.1:6379/1'),
    }
}

# Email Configuration — SendGrid
EMAIL_BACKEND = 'sendgrid_backend.SendgridBackend'
SENDGRID_API_KEY = os.getenv('SENDGRID_API_KEY', '')
SENDGRID_SANDBOX_MODE_IN_DEBUG = False
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'TrackRival <noreply@trackrival.app>')


# ---------------------------------------------------------------------------
# HTTPS / cookie hardening. Set USE_HTTPS=True once the site is served over TLS.
# ---------------------------------------------------------------------------
USE_HTTPS = os.getenv('USE_HTTPS', 'False').strip().lower() == 'true'
if USE_HTTPS:
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', '31536000'))
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

SECURE_CONTENT_TYPE_NOSNIFF = True
SESSION_COOKIE_HTTPONLY = True
X_FRAME_OPTIONS = 'DENY'
