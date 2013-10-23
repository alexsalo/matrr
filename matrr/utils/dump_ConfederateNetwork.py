#import sys
#this = sys.modules[__name__]
#for n in dir():
#    if n[0]!='_': delattr(this, n)
import os, sys
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrr.settings")

from network_tools import ConfederateNetwork
from matplotlib import pyplot
from matrr.models import Cohort

cohort_pk = int(sys.argv[1]) # 0 index is this file's filename
cfn = ConfederateNetwork(Cohort.objects.get(pk=cohort_pk))
cfn.network.layout(prog='dot')
cfn.network.draw('ConfederateNetwork.%d.png' % cohort_pk)
cfn.network.close()
pyplot.clf()