import sys
import os
sys.path.append('/web/www/matrr-prod')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrr.settings")
import django
django.setup()

from matrr import settings
from matrr.emails import send_verify_tissues_info

if settings.PRODUCTION:
	send_verify_tissues_info()
