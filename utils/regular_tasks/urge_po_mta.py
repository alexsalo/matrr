import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
from matrr import settings
setup_environ(settings)

from matrr.emails import urge_po_mta

if settings.PRODUCTION:
	urge_po_mta()