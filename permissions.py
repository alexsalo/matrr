import sys, os
project =  os.path.dirname(os.path.realpath(__file__))
sys.path.append(project)
from django.core.management import setup_environ
import settings
setup_environ(settings)

from django.contrib.contenttypes.models import ContentType
from django.contrib.auth.models import Permission

def sync_permissions():
	cts =  ContentType.objects.all()
	for ct in cts:
		perms = ct.model_class()._meta.permissions
		if perms:
			for codename, desc in perms:
				perm, created = Permission.objects.get_or_create(content_type=ct, codename=codename)
				if created:
					perm.name=desc
					perm.save()
		

sync_permissions()
