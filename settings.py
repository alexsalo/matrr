import os

path = os.path.dirname(os.path.realpath(__file__))

DEBUG = False
TEMPLATE_DEBUG = DEBUG

ADMINS = (
# ('Your Name', 'your_email@example.com'),
)

if path == '/web/www/matrr-prod':
    PRODUCTION = True
elif path == '/web/www/matrr-dev':
    DEVELOPMENT = GLEEK = True
else:
    DEVELOPMENT = True



DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql_psycopg2',
            # Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
            'NAME': 'matrr_production', # Or path to database file if using sqlite3.
            'USER': 'matrr_prod', # Not used with sqlite3.
            'PASSWORD': 'm0nk3y_1s_drUnK', # Not used with sqlite3.
            'HOST': 'localhost', # Set to empty string for localhost. Not used with sqlite3.
            #'PORT': '',                      # Set to empty string for default. Not used with sqlite3.
        }
}

TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale
USE_L10N = True

MEDIA_ROOT = '/web/www/MATRR/prod/media'
MEDIA_URL = '/media/'
STATIC_ROOT = '/web/www/MATRR/prod/static'
STATIC_URL = '/static/'
ADMIN_MEDIA_PREFIX = '/static/admin/'
STATICFILES_DIRS = (
        path + '/static',
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
    "django.contrib.auth.context_processors.auth",
    "django.core.context_processors.debug",
    "django.core.context_processors.i18n",
    "django.core.context_processors.media",
    "django.core.context_processors.static",
    "django.core.context_processors.request",
    'matrr.context_processors.cart',
    'matrr.context_processors.login_form',
    'matrr.context_processors.group_membership',
    'matrr.context_processors.unsupported_browser'
    )

TEMPLATE_DIRS = (
    # Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
    path + "/templates",
    path + "/templates/matrr",
    )

SPHINX_API_VERSION = 0x116
SPHINX_SERVER = 'localhost'
SPHINX_PORT = 9312
SEARCH_INDEXES = {'monkey':"monkey", 'monkey_auth':"monkey_auth", 'cohort':"cohort"}

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

ACCOUNT_ACTIVATION_DAYS = 2
EMAIL_HOST = 'localhost'
DEFAULT_FROM_EMAIL = 'matrr_admin@localhost'

LOGIN_REDIRECT_URL = '/accounts/login'

if DEVELOPMENT:
    from develop_settings import *

