# Django settings for matrr project.
import logging
import os
import getpass
import traceback
import sys

path = os.path.dirname(os.path.realpath(__file__))

DEBUG = False
#DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
('matrr_admin', 'matrrgleek@gmail.com'),
)
MANAGERS = ADMINS

GLEEK = False
DEVELOPMENT = False
PRODUCTION = False

if path == '/web/www/matrr-prod/matrr':
    PRODUCTION = True
    GLEEK = True
elif path == '/web/www/matrr-dev/matrr':
    DEVELOPMENT = True
    GLEEK = True
else:
    DEVELOPMENT = True

ENABLE_EMAILS = not DEBUG
INCLUDE_SITEWIDE_WARNING = False

# I can't remember why I added this
# I think it has to do with dot-files in the project dir
# to my knowledge the project is never used as root.
if getpass.getuser().lower() == 'root':
    if PRODUCTION:
        os.environ['HOME'] = "/web/www/matrr-prod"
    if DEVELOPMENT:
        os.environ['HOME'] = "/web/www/matrr-dev"
if GLEEK:
    import matplotlib
    matplotlib.use('agg')



DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'matrr_production',
        'USER': 'matrr_prod',
        'PASSWORD': 'm0nk3y_1s_drUnK',
        'HOST': '10.4.100.2',
    }
}

# This view is what handled a failed CSRF test, pointing users to the FAQ page
# for instructions on how to enable cookies.  This worked in 1.3 (woohoo!), it
# should still work in 1.5 (I didn't see any release notes related to it).  I
# believe there are more versitle error handling mechanics in 1.4+, if this doesn't
# work in 1.5+
CSRF_FAILURE_VIEW = 'matrr.views.basic.matrr_handler403'

# Hosts/domain names that are valid for this site; required if DEBUG is False
# See https://docs.djangoproject.com/en/1.5/ref/settings/#allowed-hosts
ALLOWED_HOSTS = ['.gleek.ecs.baylor.edu', '.matrr.com']

# Local time zone for this installation. Choices can be found here:
# http://en.wikipedia.org/wiki/List_of_tz_zones_by_name
# although not all choices may be available on all operating systems.
# In a Windows environment this must be set to your system time zone.
TIME_ZONE = 'America/Chicago'

# Language code for this installation. All choices can be found here:
# http://www.i18nguy.com/unicode/language-identifiers.html
LANGUAGE_CODE = 'en-us'

SITE_ID = 1

# If you set this to False, Django will make some optimizations so as not
# to load the internationalization machinery.
USE_I18N = True

# If you set this to False, Django will not format dates, numbers and
# calendars according to the current locale.
USE_L10N = True

# If you set this to False, Django will not use timezone-aware datetimes.
USE_TZ = False

UPLOAD_DIR = '/web/www/MATRR/prod/upload'

# Absolute filesystem path to the directory that will hold user-uploaded files.
# Example: "/var/www/example.com/media/"
MEDIA_ROOT = '/web/www/MATRR/prod/media'

# URL that handles the media served from MEDIA_ROOT. Make sure to use a
# trailing slash.
# Examples: "http://example.com/media/", "http://media.example.com/"
MEDIA_URL = '/media/'

# Absolute path to the directory static files should be collected to.
# Don't put anything in this directory yourself; store your static files
# in apps' "static/" subdirectories and in STATICFILES_DIRS.
# Example: "/var/www/example.com/static/"
STATIC_ROOT = '/web/www/MATRR/prod/static'

# URL prefix for static files.
# Example: "http://example.com/static/", "http://static.example.com/"
STATIC_URL = '/static/'

MATRR_STATIC_STRING = 'static'
ADMIN_MEDIA_PREFIX = '/' + MATRR_STATIC_STRING + '/admin/'

# Additional locations of static files
STATICFILES_DIRS = (
    # Put strings here, like "/home/html/static" or "C:/www/django/static".
    # Always use forward slashes, even on Windows.
    # Don't forget to use absolute paths, not relative paths.
	  os.path.join(path, MATRR_STATIC_STRING),
	)

# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
#	'django.contrib.staticfiles.finders.DefaultStorageFinder',
	)

# List of regex URLs which do NOT require user to be logged in.
# Your Login URL MUST be included.
PUBLIC_URLS = (
	r'^$',
	r'^logout/?$',
	r'^accounts/', # django.auth url, NOT matrr's "account" url.  -.-
	r'^(privacy|data|usage|browser|public-faq|about|benefits|denied|not-verified)/', # all non-dynamic pages.  Should find a way to pull this from matrr.urls
	r'^contact_us/$',
	r'^publications/$',
	r'^cohort/(?P<cohort_id>\d+)/$',
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

	'matrr.middleware.EnforceLoginMiddleware',
	)

ROOT_URLCONF = 'matrr.urls'

TEMPLATE_CONTEXT_PROCESSORS = [
	"django.contrib.auth.context_processors.auth",
	"django.core.context_processors.debug",
	"django.core.context_processors.i18n",
	"django.core.context_processors.media",
	"django.core.context_processors.static",
	"django.core.context_processors.request",
	'matrr.context_processors.cart',
	'matrr.context_processors.login_form',
	'matrr.context_processors.global_context',
	'matrr.context_processors.unsupported_browser',
    'django.contrib.messages.context_processors.messages',
]
if INCLUDE_SITEWIDE_WARNING:
    TEMPLATE_CONTEXT_PROCESSORS.append('matrr.context_processors.include_sitewide_warning')

TEMPLATE_DIRS = (
	# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
	path + "/templates",
	path + "/templates/matrr",
	"/web/www/MATRR/prod/media/matrr_images/fragments",
	)

# Python dotted path to the WSGI application used by Django's runserver.
WSGI_APPLICATION = 'matrr.wsgi.application'

SESSION_SERIALIZER = 'django.contrib.sessions.serializers.JSONSerializer'

SPHINX_API_VERSION = 0x116
SPHINX_SERVER = '10.4.100.2'
SPHINX_PORT = 9312

INSTALLED_APPS = (
		'django.contrib.auth',
		'django.contrib.contenttypes',
		'django.contrib.sessions',
		'django.contrib.sites',
		'django.contrib.messages',
		'django.contrib.staticfiles',
		'django.contrib.admin',
		'django.contrib.admindocs',

		'matrr',
		'registration',
		'south',
		)

ACCOUNT_ACTIVATION_DAYS = 2
EMAIL_HOST = 'localhost'
DEFAULT_FROM_EMAIL = 'matrr_admin@localhost'

LOGIN_REDIRECT_URL = '/'

PUBLIC_SEARCH_INDEXES = {'monkey':("monkey", 'Monkey'),
						 'cohort':("cohort", 'Cohort'),
						 'publications': ('publications', 'Publication'),
						 'monkeyprotein': ('monkeyprotein', 'MonkeyProtein')}
PRIVATE_SEARCH_INDEXES = {'monkey_auth':("monkey_auth", 'Monkey')}

# These define the grace periods following a tissue shipment and a RUD submission
# before we start emailing the user to submit a ResearchUpdate
ResearchUpdateInitialGrace = 90
ResearchUpdateNoProgressGrace = 45
ResearchUpdateInProgressGrace = 180

# A sample logging configuration. The only tangible logging
# performed by this configuration is to send an email to
# the site admins on every HTTP 500 error when DEBUG=False.
# See http://docs.djangoproject.com/en/dev/topics/logging for
# more details on how to customize your logging configuration.
#
# Modified per suggestions from http://stackoverflow.com/questions/238081/how-do-you-log-server-errors-on-django-sites
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
        'logfile': {
            'class': 'logging.handlers.WatchedFileHandler',
            'filename': '/web/www/matrr-prod/MATRR.log'
        },
    },
    'loggers': {
        'django.request': {
            'handlers': ['mail_admins'],
            'level': 'ERROR',
            'propagate': True,
        },
        # Might as well log any errors anywhere else in Django
        'django': {
            'handlers': ['logfile'],
            'level': 'ERROR',
            'propagate': False,
        },
    }
}

## My logging
#_log_path = os.environ['HOME']
#_log_file = 'MATRR.log'
#LOG_FILE_PATH = os.path.join(_log_path, _log_file)
## this logger will only get hit by django if debug == False.  I think django wraps everything in a try:catch
#logging.basicConfig(format='%(asctime)s|%(levelname)s|%(message)s', datefmt='%Y-%m-%d %H:%M:%S', filename=LOG_FILE_PATH, level=logging.WARNING)
#
#def log_except_hook(*exc_info):
#    text = "".join(traceback.format_exception(*exc_info))
#    logging.error("Unhandled exception: %s", text)
#
#if GLEEK:
#    sys.excepthook = log_except_hook



if DEVELOPMENT:
    from develop_settings import *
