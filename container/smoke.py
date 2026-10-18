"""Offline image startup/import check with synthetic settings and memory queues."""
import importlib.metadata
import json
import os
import types
import sys

from obcollection.settings import base

settings = types.ModuleType('image_smoke_settings')
for name in dir(base):
    if name.isupper():
        setattr(settings, name, getattr(base, name))
settings.SECRET_KEY = 'synthetic-offline-image-check'
settings.DEBUG = False
settings.SITE_HOST_NAME = 'testserver'
settings.ALLOWED_HOSTS = ['testserver']
settings.DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3', 'NAME': ':memory:'}}
settings.STATIC_ROOT = '/tmp/static'
settings.STATIC_URL = '/static/'
settings.MEDIA_ROOT = '/tmp/media'
settings.EMAIL_BACKEND = 'django.core.mail.backends.locmem.EmailBackend'
settings.HUEY_EMAIL_BACKEND = settings.EMAIL_BACKEND
settings.HUEY = {'huey_class': 'huey.MemoryHuey', 'name': 'image-smoke', 'immediate': False}
settings.CACHES = {name: {'BACKEND': 'django.core.cache.backends.locmem.LocMemCache', 'LOCATION': name}
                   for name in ['default', 'select2']}
settings.SELECT2_CACHE_BACKEND = 'select2'
settings.MEILISEARCH_CLIENT = {'url': 'http://127.0.0.1:9'}
settings.MEILISEARCH_INDEX = 'content'
settings.USE_RECAPTCHA = False
for name in ['RECAPTCHA_KEY', 'GOOGLE_PROJECT_ID', 'YOUTUBE_API_KEY',
             'SPOTIFY_CLIENT_ID', 'SPOTIFY_CLIENT_SECRET']:
    setattr(settings, name, '')
settings.LOGGING = {'version': 1, 'disable_existing_loggers': True}
sys.modules[settings.__name__] = settings
os.environ['DJANGO_SETTINGS_MODULE'] = settings.__name__
import django
django.setup()
from django.core.management import call_command
call_command('check')
from obcollection.wsgi import application
from huey.contrib.djhuey import HUEY
from huey.contrib.djhuey.management.commands.run_huey import Command
import obpages.tasks
import obpages.accounts.tasks
assert callable(application) and Command
assert HUEY.storage.__class__.__name__ == 'MemoryStorage'
assert os.getuid() == 373
print(json.dumps({'offline_wsgi_startup': True, 'worker_task_imports': True,
                  'uid': os.getuid(), 'django': django.get_version(),
                  'packages': {name: importlib.metadata.version(name) for name in
                               ['django-overcomingbias-api', 'django-overcomingbias-pages',
                                'django-overcomingbias-collection']}}))
