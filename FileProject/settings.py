"""
Django settings for FileProject project.

Generated by 'django-admin startproject' using Django 4.0.6.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""
import sys
from pathlib import Path
# import djcelery
# djcelery.setup_loader()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = 'django-insecure-rfad_z0nf$$*t98%i)jg4b%$+-dvez&qq)yyeqmw0^h)z#^j@n'

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = True

ALLOWED_HOSTS = []


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'count.apps.CountConfig',
    'rest_framework',
    'django_filters',
    'django_celery_results',
    # 'djcelery',
]

REST_FRAMEWORK = {
    'DEFAULT_FILTER_BACKENDS': (
        'django_filters.rest_framework.DjangoFilterBackend',
    )
}

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'FileProject.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates']
        ,
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

WSGI_APPLICATION = 'FileProject.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
"""orginal Database definition"""
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'file_db',
        'USER': 'zahra',
        'PASSWORD': '1234',
        'HOST': 'localhost',
        'PORT': '5432',
        'TEST': {
            'NAME': "mytest"
        }
    }
}

"""this is a manually database definition :"""
# if sys.argv[1:2] == ['test']:
# if 'test' in sys.argv:
#     DATABASES["default"] = {
#         'ENGINE': 'django.db.backends.sqlite3',
#         'NAME': 'file_db',
#         'USER': 'zahra',
#         'PASSWORD': '1234',
#         'HOST': 'localhost'
#     }


# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True

# 3 below lines didn't save task result in DB
# CELERY_RESULT_BACKEND = "redis://localhost:6379"  # django-cache  # "postgresql://localhost:5432"
# CELERY_RESULT_BACKEND = 'db+postgresql://zahra:1234@localhost/django_celery_results_TaskResult'
# CELERY_RESULT_BACKEND = 'postgresql://localhost:5432'
CELERY_RESULT_BACKEND = 'django-db'
CELERY_BROKER_URL = "redis://localhost:6379"
CELERY_CACHE_BACKEND = 'django-cache'  # 'default'
# CACHES = {
#     'default': {
#         'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
#         'LOCATION': 'my_cache_table',
#     }
# }
# do for above CACHES setting: python manage.py createcachetable --dry-run

# TEST_RUNNER = 'djcelery.contrib.test_runner.CeleryTestSuiteRunner'

# two below lines  lonely don't help to save task results model in tests:
# CELERY_TASK_ALWAYS_EAGER = True
# CELERY_TASK_STORE_EAGER_RESULT = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = 'static/'

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'
