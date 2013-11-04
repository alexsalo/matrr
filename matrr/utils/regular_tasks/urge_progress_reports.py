import sys
import os
print sys.path
sys.path.append('/web/www/matrr-prod')
print sys.path
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrr.settings")

from matrr import settings
from matrr.emails import urge_progress_reports

if settings.PRODUCTION:
	raise Exception()
	urge_progress_reports()
