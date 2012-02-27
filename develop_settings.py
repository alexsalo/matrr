import os

# get the location of this settings file
# this will let us have different settings based on where the file is
path = os.path.dirname(os.path.realpath(__file__))

DEBUG = True
TEMPLATE_DEBUG = DEBUG

DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			# Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
			'NAME': 'matrr_development', # Or path to database file if using sqlite3.
			'USER': 'matrr_develop', # Not used with sqlite3.
			'PASSWORD': 'PsNvAMDt91', # Not used with sqlite3.
			'HOST': 'localhost', # Set to empty string for localhost. Not used with sqlite3.
			#'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
		}
    }
UPLOAD_DIR = '/web/www/MATRR/dev/upload'
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

# Jon added this on 11/15/2011 to see if it'll make VIP pages work
TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path + "/templates",
    path + "/templates/matrr",
	"/web/www/MATRR/dev/media/matrr_images/fragments",
    )
## --end jon add

PUBLIC_SEARCH_INDEXES = {'monkey':("d_monkey", 'Monkey'),
						 'cohort':("d_cohort", 'Cohort'),
						 'publications': ('d_publications', 'Publication'),
						 'monkeyprotein': ('d_monkeyprotein', 'MonkeyProtein')}
PRIVATE_SEARCH_INDEXES = {'monkey_auth':("d_monkey_auth", 'Monkey')}

try:
    from local_settings import *
except:
    pass