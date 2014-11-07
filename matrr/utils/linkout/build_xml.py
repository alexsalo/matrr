from django.template import Context, loader
from matrr.models import Cohort
from django.db.models import Count

def build_resource_xml(file_name='resources.xml'):
	temp = loader.get_template("linkout/resources.xml")
	cohorts = Cohort.objects.annotate(num_pubs=Count('publication_set')).filter(num_pubs__gte=1)
	c = Context({"cohorts": cohorts})
	xml =  temp.render(c)
	with open(file_name, 'w') as f:
		f.write(xml)
	