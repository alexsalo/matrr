import sys
import os
sys.path.append('/web/www/matrr-prod')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrr.settings")

from matrr import settings
from matrr.emails import send_colliding_requests_info

if settings.PRODUCTION:
	send_colliding_requests_info()
