import os
import sys

# To activate virtualenv uncomment next two lines
#activate_this = '/web/www/matrr-dev/ve/bin/activate_this.py'
#execfile(activate_this, dict(__file__=activate_this))

path = os.path.dirname( os.path.realpath( __file__ ) )
if path not in sys.path:
    sys.path.append(path)

os.environ['DJANGO_SETTINGS_MODULE'] = 'settings'

import django.core.handlers.wsgi
application = django.core.handlers.wsgi.WSGIHandler()
