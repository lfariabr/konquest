import os
from pathlib import Path
from decouple import config

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent
SECRET_KEY = config('SECRET_KEY')
DEBUG = True
CSRF_TRUSTED_ORIGINS = [
    'https://konquista.com.br',
    'https://www.konquista.com.br',
    'http://konquista.com.br',
    'http://www.konquista.com.br'
]

ALLOWED_HOSTS = ['konquista.com.br', 'www.konquista.com.br', '209.38.90.25', 'localhost']

WSGI_APPLICATION = 'konquist.wsgi.application'

# DATABASE: sqlite3 (dev) OR postgresql (prod)
DATABASE_ENGINE = 'postgresql' 
CONTACTS_START = 121
CONTACTS_END = 300

CONTACTS_TO_LOAD = 700 # messageShooter/resolvers/get_contacts.py
CONTACTS_TO_LOAD_APT = 3000

INSTALLED_APPS = [
    'django_daisy',
    'jazzmin',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Extra Libraries
    'rest_framework',
    'graphene_django',
    # 'debug_toolbar',

    # Apps
    'django_celery_beat',
    'apiCrm',
    'core',
    'apiSocialHub',
    'dataWrestler',

    # Controller:
    'messageShooter'
]

MIDDLEWARE = [
    'django.middleware.cache.UpdateCacheMiddleware',  # Add this first - performance
    # 'debug_toolbar.middleware.DebugToolbarMiddleware', 
    'django.middleware.security.SecurityMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'django.middleware.cache.FetchFromCacheMiddleware',  # Add this last - performance

]

ROOT_URLCONF = 'konquist.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            os.path.join(BASE_DIR, 'frontend', 'templates'),
            os.path.join(BASE_DIR, 'dataWrestler', 'templates'),
        ],
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

if DATABASE_ENGINE == 'postgresql':
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': config('DB_NAME'),
            'USER': config('DB_USER'),
            'PASSWORD': config('DB_PASSWORD'),
            'HOST': config('DB_HOST'),
            'PORT': config('DB_PORT', default='5432'),
            'CONN_MAX_AGE': 60,  # 60 seconds connection lifetime
            'OPTIONS': {
                'connect_timeout': 10,
                'keepalives': 1,
                'keepalives_idle': 30,
                'keepalives_interval': 10,
                'keepalives_count': 5,
            }
        }
    }

else:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# Database optimization settings
DATABASE_OPTIONS = {
    'timeout': 30,  # 30 seconds
    'connect_timeout': 10
}

# Query optimization
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10240

# Cache middleware settings
CACHE_MIDDLEWARE_ALIAS = 'default'
CACHE_MIDDLEWARE_SECONDS = 300
CACHE_MIDDLEWARE_KEY_PREFIX = ''

# Django Daisy Configuration
APPS_REORDER = {}

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Password validation
# https://docs.djangoproject.com/en/5.1/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {
            'min_length': 9,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]


# Internationalization
# https://docs.djangoproject.com/en/5.1/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'America/Sao_Paulo'
USE_TZ = True
USE_I18N = True



# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/5.1/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')
STATICFILES_DIRS = [
    os.path.join(BASE_DIR, 'frontend', 'static'),
]

# Media Files (to send messages):
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'core', 'media')
DATA_UPLOAD_MAX_MEMORY_SIZE = 104857600  # 100 MB

# Default primary key field type
# https://docs.djangoproject.com/en/5.1/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '[{asctime}] {levelname} {name} {message}',
            'style': '{',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'messageShooter': {  
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'core': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': False,
        },
        'apiCrm': {
            'handlers': ['console'],
            'level': 'DEBUG',  # Set to DEBUG to see all logs
            'propagate': True,
        },
        'celery': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
    'root': {
        'handlers': ['console'],
        'level': 'WARNING',
    }
}

# Redis Configuration
REDIS_HOST = config('REDIS_HOST', default='redis')
REDIS_PORT = config('REDIS_PORT', default='6379')
REDIS_PASSWORD = config('REDIS_PASSWORD', default='')
REDIS_DB = '0'

REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}'
CELERY_BROKER_URL = f'{REDIS_URL}/{REDIS_DB}'
CELERY_RESULT_BACKEND = REDIS_URL

# # Redis Configuration
# REDIS_HOST = os.environ.get('REDIS_HOST', 'redis')
# REDIS_PORT = os.environ.get('REDIS_PORT', '6380')
# REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD', '')
# REDIS_DB = '0'

# REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}'
# CELERY_BROKER_URL = f'{REDIS_URL}/{REDIS_DB}'
# CELERY_RESULT_BACKEND = REDIS_URL

# Celery Configuration
CELERY_TIMEZONE = 'America/Sao_Paulo'
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60

# Debug toolbar settings
INTERNAL_IPS = [
    '127.0.0.1',
]

if DEBUG:
    DEBUG_TOOLBAR_CONFIG = {
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        'RESULTS_CACHE_SIZE': 3,
        'ENABLE_STACKTRACES': False,
    }
    
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.profiling.ProfilingPanel',
    ]

# Cache Settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': REDIS_URL,
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'MAX_ENTRIES': 1000,
            'CULL_FREQUENCY': 3,
        }
    }
}