import os
path = os.path.dirname(os.path.realpath(__file__))

DEBUG = False
#DEBUG = True
TEMPLATE_DEBUG = DEBUG

ADMINS = (
# ('Your Name', 'your_email@example.com'),
)
GLEEK = DEVELOPMENT = PRODUCTION = False

if path == '/web/www/matrr-prod':
	PRODUCTION = True
	
elif path == '/web/www/matrr-dev':
	DEVELOPMENT = GLEEK = True
else:
	DEVELOPMENT = True

#if PRODUCTION or GLEEK:
import getpass

if getpass.getuser().lower() == 'root':
	if PRODUCTION:
		os.environ['HOME'] = "/web/www/matrr-prod"
	if DEVELOPMENT:
		os.environ['HOME'] = "/web/www/matrr-dev"	
import matplotlib
matplotlib.use('Agg')
DATABASES = {
		'default': {
			'ENGINE': 'django.db.backends.postgresql_psycopg2',
			# Add 'postgresql_psycopg2', 'postgresql', 'mysql', 'sqlite3' or 'oracle'.
			'NAME': 'matrr_production', # Or path to database file if using sqlite3.
			'USER': 'matrr_prod', # Not used with sqlite3.
			'PASSWORD': 'm0nk3y_1s_drUnK', # Not used with sqlite3.
			'HOST': '10.4.100.2', # Set to empty string for localhost. Not used with sqlite3.
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
UPLOAD_DIR = '/web/www/MATRR/prod/upload'
MEDIA_ROOT = '/web/www/MATRR/prod/media'
MEDIA_URL = '/media/'
STATIC_ROOT = '/web/www/MATRR/prod/static'
STATIC_URL = '/static/'
MATRR_STATIC_STRING = 'static'
ADMIN_MEDIA_PREFIX = '/' + MATRR_STATIC_STRING + '/admin/'
STATICFILES_DIRS = (
	  os.path.join(path, MATRR_STATIC_STRING),
	)
# List of finder classes that know how to find static files in
# various locations.
STATICFILES_FINDERS = (
	'django.contrib.staticfiles.finders.FileSystemFinder',
	'django.contrib.staticfiles.finders.AppDirectoriesFinder',
	'django.contrib.staticfiles.finders.DefaultStorageFinder',
	)

# List of regex URLs which do NOT require user to be logged in.
# Your Login URL MUST be included. 
PUBLIC_URLS = (
	r'^$',
	r'^login/?$',
	r'^logout/?$',
	r'^accounts/', # django.auth url, NOT matrr's "account" url.  -.-
	r'^(privacy|data|usage|browser|public-faq|about|benefits|denied|not-verified)/', # all non-dynamic pages.  Should find a way to pull this from matrr.urls
	r'^contact_us/$',
	r'^publications/$',
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

#	'matrr.middleware.LoginRequiredMiddleware',
#	'matrr.middleware.RequireLoginMiddleware'
	'matrr.middleware.EnforceLoginMiddleware',
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
	'matrr.context_processors.unsupported_browser',

#	"django.core.context_processors.auth",
	)

TEMPLATE_DIRS = (
	# Put strings here, like "/home/html/django_templates" or "C:/www/django/templates".
	# Always use forward slashes, even on Windows.
	# Don't forget to use absolute paths, not relative paths.
	path + "/templates",
	path + "/templates/matrr",
	"/web/www/MATRR/prod/media/matrr_images/fragments",
	)

SPHINX_API_VERSION = 0x116
SPHINX_SERVER = '10.4.100.2'
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

LOGIN_REDIRECT_URL = '/'

if DEVELOPMENT:
	from develop_settings import *
