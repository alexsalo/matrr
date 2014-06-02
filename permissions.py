import sys
import os
sys.path.append('/web/www/matrr-prod')
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "matrr.settings")

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
                perm, created = Permission.objects.get_or_create(content_type=ct, codename=codename)
                if created:
                    perm.name=desc
                    perm.save()
                    print "Created Permission: %s: %s" % (ct.model_class(), desc)
    stale_permissions = list()
    for perm in Permission.objects.all():
        if perm.content_type.app_label != 'matrr':
            continue
        model_class = perm.content_type.model_class()
        perm_lookup = (perm.codename, perm.name)
        if perm.codename == 'add_%s' % perm.content_type.model:
            continue
        if perm.codename == 'change_%s' % perm.content_type.model:
            continue
        if perm.codename == 'delete_%s' % perm.content_type.model:
            continue
        if perm_lookup in model_class._meta.permissions:
            continue
        else:
            stale_permissions.append(perm)
    print "You should delete these permissions, they're old."
    for perm in stale_permissions:
        print "pk=%d, %s - %s" % (perm.pk, perm.codename, perm.name)

sync_permissions()
