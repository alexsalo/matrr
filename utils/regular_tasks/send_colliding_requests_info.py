import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)

from matrr.emails import send_colliding_requests_info

if settings.PRODUCTION:
	send_colliding_requests_info()
