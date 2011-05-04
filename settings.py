# Django settings for MATRR project.

import os

# get the location of this settings file
# this will let us have different settings based on where the file is
path = os.path.dirname( os.path.realpath( __file__ ) )

DEVELOPMENT = TEST = PRODUCTION = False
if path == '/web/django_test':
  DEVELOPMENT = True
elif path == '/web/www/dev':
  TEST = True
elif path == '/web/www/wsgi-scripts':
  PRODUCTION = True


if DEVELOPMENT or TEST:
  DEBUG = True
else:
  DEBUG = False
TEMPLATE_DEBUG = DEBUG

SITE_ROOT = ''
if TEST:
  SITE_ROOT = '/dev'

ADMINS = (
    # ('Your Name', 'your_email@example.com'),
)

MANAGERS = ADMINS

if TEST:
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
          'NAME': 'matrr_test',                      # Or path to database file if using sqlite3.
          'USER': 'django_test',                      # Not used with sqlite3.
          'PASSWORD': 'matrr_django',                  # Not used with sqlite3.
          'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
          #'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
      }
  }
else:
  DATABASES = {
      'default': {
          'ENGINE': 'django.db.backends.postgresql_psycopg2', # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
          'NAME': 'django_test',                      # Or path to database file if using sqlite3.
          'USER': 'django_test',                      # Not used with sqlite3.
          'PASSWORD': 'matrr_django',                  # Not used with sqlite3.
          'HOST': 'localhost',                      # Set to empty string for localhost. Not used with sqlite3.
          #'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
      }
  }


# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# On Unix systems, a value of None will cause Django to use the same
# timezone as the operating system.
# If running in a Windows environment this must be set to the same as your
# system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

if TEST:
  SITE_ID = 2
else:
  SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/home/media/media.lawrence.com/media/"
MEDIA_ROOT = '/web/django_test/media/'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://media.lawrence.com/media/", "http://example.com/media/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/home/media/media.lawrence.com/static/"
STATIC_ROOT = ''

# URL prefix for static files.
# Example: "http://media.lawrence.com/static/"
STATIC_URL = '/static/'

# URL prefix for admin static files -- CSS, JavaScript and images.
# Make sure to use a trailing slash.
# Examples: "http://foo.com/static/admin/", "/static/admin/".
ADMIN_MEDIA_PREFIX = '/static/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    '/web/django_test/static/',
)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
    'django.contrib.staticfiles.finders.DefaultStorageFinder',
)

# Make this unique, and don't share it with anybody.
SECRET_KEY = '@+5ijd@xf%17@7euip67u)%(fq4+3g(83+azo3ia7^f=-(w1u2'

# List of callables that know how to import templates from various sources.
TEMPLATE_LOADERS = (
    'django.template.loaders.filesystem.Loader',
    'django.template.loaders.app_directories.Loader',
    'django.template.loaders.eggs.Loader',
)

MIDDLEWARE_CLASSES = (
    'django.middleware.common.CommonMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.transaction.TransactionMiddleware',
)

ROOT_URLCONF = 'urls'

TEMPLATE_CONTEXT_PROCESSORS = (
    "django.core.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    'matrr.context_processors.cart',
    'matrr.context_processors.login_form',
    'matrr.context_processors.group_membership',
    'matrr.context_processors.site_root',
)

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path + "/templates",
)

# Sphinx 0.9.9
SPHINX_API_VERSION = 0x116

if DEVELOPMENT:
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
else:
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
      'utils',
      'south',
  )

# The following are settings for django-registration
# added EJB 3.16.11
# account_activation is the number of days the email
# is active, it is really the only setting that
# is technically required

ACCOUNT_ACTIVATION_DAYS = 2
EMAIL_HOST = 'localhost'
DEFAULT_FROM_EMAIL = 'matrr_admin@localhost'

LOGIN_REDIRECT_URL = '/accounts/login'

if DEVELOPMENT:
  import logging
  logging.basicConfig(
      level = logging.DEBUG,
      format = '%(asctime)s %(levelname)s %(message)s',
      filename='/web/mattr.log',
      filemode='a'
  )


# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler'
        }
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
    }
}
