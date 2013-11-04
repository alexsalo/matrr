import sys
import os
sys.path.append('/web/www/matrr-prod')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrr.settings")

from matrr import settings
from matrr.emails import urge_progress_reports

if settings.PRODUCTION:
	raise Exception()
	urge_progress_reports()
