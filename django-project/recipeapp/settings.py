"""
Django settings for recipeapp project.

This module contains all Django configuration for the recipes project,
including database, middleware, installed apps, and more.

The configuration supports multiple database backends:
1. SQLite (default for local development)
2. PostgreSQL (for production and advanced features)

Database selection is determined by environment variables:
- If DATABASE_URL is set (Render, Heroku), it takes precedence
- Otherwise, DB_ENGINE determines the backend:
  - 'sqlite' (default) uses SQLite
  - 'postgresql' uses PostgreSQL
"""

from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent


# SECURITY WARNING: keep the secret key used in production secret!
# Generate a new key for production using: python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())'
SECRET_KEY = os.getenv('SECRET_KEY', 'django-insecure-change-me-in-production')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.getenv('DEBUG', 'True') == 'True'

# In production, set ALLOWED_HOSTS to your domain name(s)
# Allow Render to set this via environment variable
ALLOWED_HOSTS = os.getenv('ALLOWED_HOSTS', 'localhost,127.0.0.1').split(',')


# Application definition

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'recipes',
]

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Serve static files efficiently
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'recipeapp.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
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

WSGI_APPLICATION = 'recipeapp.wsgi.application'


# Database
# https://docs.djangoproject.com/en/4.2/ref/settings/#databases
#
# Database configuration priority (highest to lowest):
# 1. DATABASE_URL environment variable (used by Render, Heroku, etc.)
# 2. DB_ENGINE with individual DB_* variables (PostgreSQL/SQLite)
# 3. Default to SQLite for local development
#
# DATABASE_URL format examples:
#   - postgres://user:password@localhost:5432/dbname
#   - sqlite:///path/to/db.sqlite3
#
# To use PostgreSQL locally, set in .env:
#   DB_ENGINE=postgresql
#   DB_NAME=recipeapp_db
#   DB_USER=postgres
#   DB_PASSWORD=postgres
#   DB_HOST=localhost
#   DB_PORT=5432
import dj_database_url

# First, support a single DATABASE_URL environment variable (used by Render, Heroku, etc.)
DATABASE_URL = os.getenv('DATABASE_URL')
if DATABASE_URL:
    # Parse the DATABASE_URL into Django's DATABASES setting
    DATABASES = {
        'default': dj_database_url.parse(DATABASE_URL, conn_max_age=600)
    }
else:
    # Fallback to per-variable DB config. Use SQLite by default for local development.
    DB_ENGINE = os.getenv('DB_ENGINE', 'sqlite')

    if DB_ENGINE == 'postgresql':
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.getenv('DB_NAME', 'recipeapp_db'),
                'USER': os.getenv('DB_USER', 'postgres'),
                'PASSWORD': os.getenv('DB_PASSWORD', 'postgres'),
                'HOST': os.getenv('DB_HOST', 'localhost'),
                'PORT': os.getenv('DB_PORT', '5432'),
            }
        }
    else:
        # SQLite for easy local development
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }


# Password validation
# https://docs.djangoproject.com/en/4.2/ref/settings/#auth-password-validators

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
# https://docs.djangoproject.com/en/4.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.2/howto/static-files/

STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'staticfiles'  # Directory where collectstatic will gather all static files

# WhiteNoise configuration for serving static files
STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

# Default primary key field type
# https://docs.djangoproject.com/en/4.2/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

