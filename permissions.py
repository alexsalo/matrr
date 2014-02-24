import sys
import os

project =  os.path.dirname(os.path.realpath(__file__))
sys.path.append(project)
from django.core.management import setup_environ
from matrr import settings
setup_environ(settings)

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

def sync_permissions():
	cts =  ContentType.objects.all()
	for ct in cts:
		try:
			perms = ct.model_class()._meta.permissions
		except:
			continue
		if perms:
			for codename, desc in perms:
				print desc
				perm, created = Permission.objects.get_or_create(content_type=ct, codename=codename)
				if created:
					perm.name=desc
					perm.save()
					print "created: %s: %s" % (ct.model_class(), desc)
		

sync_permissions()
