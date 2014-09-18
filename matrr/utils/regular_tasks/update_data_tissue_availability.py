import sys
import os
sys.path.append('/web/www/matrr-prod')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrr.settings")

from matrr import settings
from matrr.utils.database import create

if settings.PRODUCTION:
	create.create_data_tissue_tree()
