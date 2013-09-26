import sys, os
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)

from utils.network_tools import ConfederateNetwork
from matrr.models import Cohort

cohort_pk = int(sys.argv[1]) # 0 index is this file's filename
cfn = ConfederateNetwork(Cohort.objects.get(pk=cohort_pk))
cfn.network.layout(prog='dot')
cfn.network.draw('ConfederateNetwork.%d.png' % cohort_pk)
cfn.network.close()
