import os

# get the location of this settings file
# this will let us have different settings based on where the file is
path = os.path.dirname(os.path.realpath(__file__))

DEBUG = True
SEARCH_INDEXES = {'monkey':"t_monkey", 'monkey_auth':"t_monkey_auth", 'cohort':"t_cohort"}

DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'matrr_test', # Or path to database file if using sqlite3.
            'USER': 'django_test', # Not used with sqlite3.
            'PASSWORD': 'matrr_django', # Not used with sqlite3.
            'HOST': 'localhost', # Set to empty string for localhost. Not used with sqlite3.
            #'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        }
    }
MEDIA_ROOT = '/web/www/MATRR/dev/media'
STATIC_ROOT = '/web/www/MATRR/dev/static'
SPHINX_SERVER = 'localhost'
SPHINX_PORT = 9312
INSTALLED_APPS = (
        'django.contrib.auth',
        'django.contrib.contenttypes',
        'django.contrib.sessions',
        'django.contrib.sites',
        'django.contrib.messages',
        'django.contrib.staticfiles',
        # Uncomment the next line to enable the admin:
        'django.contrib.admin',
        # Uncomment the next line to enable admin documentation:
        'django.contrib.admindocs',
        'matrr',
        # django-registration installed by EJB - 3.16.11
        'registration',
        'djangosphinx',
        'utils',
        'south',
        )
try:
    from local_settings import *
except:
    pass