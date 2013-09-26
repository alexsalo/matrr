import sys
from utils.network_tools import ConfederateNetwork
from matrr.models import Cohort

cohort_pk = sys.argv[0]
assert int(cohort_pk)
cfn = ConfederateNetwork(Cohort.objects.get(pk=cohort_pk))
cfn.network.layout(prog='dot')
cfn.network.draw('ConfederateNetwork.%d.png' % cohort_pk)
