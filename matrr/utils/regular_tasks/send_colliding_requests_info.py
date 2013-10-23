import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from matrr import settings

# deprecated
from django.core.management import setup_environ
setup_environ(settings)
# test this solution:  http://stackoverflow.com/questions/17937017/updated-django-from-1-4-to-1-5-1-now-deprecationwarning-on-setup-environ

from matrr.emails import send_colliding_requests_info

if settings.PRODUCTION:
	send_colliding_requests_info()
