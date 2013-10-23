#import sys
#this = sys.modules[__name__]
#for n in dir():
#    if n[0]!='_': delattr(this, n)
import os, sys
project =  os.path.dirname(os.path.dirname(os.path.dirname(os.path.realpath(__file__))))
sys.path.append(project)

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrr.settings")

from network_tools import ConfederateNetwork, ConfederateNetwork_all_closest_bouts
from matrr.models import Cohort

for argv in sys.argv[1:]:
#    cohort_pk = int(sys.argv[1]) # 0 index is this file's filename
    for CFN in [ConfederateNetwork, ConfederateNetwork_all_closest_bouts]:
        cohort = Cohort.objects.get(pk=argv)
        cfn = CFN(cohort)
        cfn.network.layout(prog='dot')
        cfn.network.draw('%s.png' % (str(cfn)))
        cfn.network.close()
