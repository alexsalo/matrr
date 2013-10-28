import sys
sys.path.append('/web/www/matrr-prod')
from django.core.management import setup_environ
from matrr import settings

# deprecated
from django.core.management import setup_environ
setup_environ(settings)
# test this solution:  http://stackoverflow.com/questions/17937017/updated-django-from-1-4-to-1-5-1-now-deprecationwarning-on-setup-environ

from matrr.emails import urge_progress_reports

if settings.PRODUCTION:
	urge_progress_reports()