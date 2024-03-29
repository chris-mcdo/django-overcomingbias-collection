"""
Django settings for obcollection project.

Generated by 'django-admin startproject' using Django 4.0.1.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/
"""

# Application definition

INSTALLED_APPS = [
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "django.contrib.sites",
    "debug_toolbar",
    "silk",
    "django_select2",
    "huey.contrib.djhuey",
    "hueymail",
    "ordered_model",
    "obapi",
    "obpages",
    "obcollection.apps.CustomAdminConfig",
    "django.forms",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "whitenoise.middleware.WhiteNoiseMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "silk.middleware.SilkyMiddleware",
    "debug_toolbar.middleware.DebugToolbarMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
    "django.contrib.sites.middleware.CurrentSiteMiddleware",
]

ROOT_URLCONF = "obcollection.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.debug",
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

# Forms
FORM_RENDERER = "django.forms.renderers.TemplatesSetting"

WSGI_APPLICATION = "obcollection.wsgi.application"

# Custom User model
# https://docs.djangoproject.com/en/4.0/topics/auth/customizing/#substituting-a-custom-user-model

AUTH_USER_MODEL = "obpages.User"

# Login and logout URLs

LOGIN_URL = "/account/login"

LOGIN_REDIRECT_URL = "/account"

# Password validation
# https://docs.djangoproject.com/en/4.0/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        "NAME": "django.contrib.auth.password_validation"
        ".UserAttributeSimilarityValidator",
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
# https://docs.djangoproject.com/en/4.0/topics/i18n/

LANGUAGE_CODE = "en-us"

TIME_ZONE = "UTC"

USE_I18N = True

USE_TZ = True


# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/4.0/howto/static-files/

STATIC_URL = "static/"

# Default primary key field type
# https://docs.djangoproject.com/en/4.0/ref/settings/#default-auto-field

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"

# Sites framework
# https://docs.djangoproject.com/en/4.0/ref/contrib/sites/

SITE_ID = 1

# OB Pages

# Results per section for unpaginated lists
OBPAGES_RESULTS_PER_SECTION = 5

# Results per page for paginated lists
OBPAGES_RESULTS_PER_PAGE = 10


# Silk settings

# Require user to be logged in, and have relevant permission (is_staff by default)
SILKY_AUTHENTICATION = True
SILKY_AUTHORISATION = True
