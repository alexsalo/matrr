from matrr import settings
from django.core.files import File
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from matrr.forms import SymposiumFormOne, SymposiumFormTwo
from matrr.models import DataSymposium

def symposium_landing(request):
    dsm = DataSymposium.objects.filter(user=request.user)
    if dsm.count() > 0:
        messages.warning(request, "You have already registered for this meeting.")
    return render_to_response('matrr/dsm_symposium/symposium_landing.html', {}, context_instance=RequestContext(request))


def symposium_registration_pg1(request):
    if request.method == 'POST':
        form = SymposiumFormOne(data=request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            return redirect(reverse('symposium-registration-pg2', args=(form.instance.pk,)))
        else:
            messages.error(request, "Your form submission had errors.  Please make sure you've filled out all required fields.")
    else:
        form = SymposiumFormOne(account=request.user.account)
    return render_to_response('matrr/dsm_symposium/symposium_registration_pg1.html', {'form': form, }, context_instance=RequestContext(request))

def symposium_registration_pg2(request, dsm_id):
    dsm = get_object_or_404(DataSymposium, pk=dsm_id)
    if request.method == 'POST':
        form = SymposiumFormTwo(instance=dsm, data=request.POST)
        if form.is_valid():
            form.instance.user = request.user
            form.save()
            messages.success(request, "You are registered for the MATRR Data Symposium")
            return redirect(reverse('account-view'))
        else:
            messages.error(request, "Your form submission had errors.  Please make sure you've filled out all required fields.")
    else:
        form = SymposiumFormTwo(instance=dsm)
    return render_to_response('matrr/dsm_symposium/symposium_registration_pg2.html', {'form': form, }, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.view_symposium_roster'), login_url='/denied/')
def symposium_roster(request):
    dsms = DataSymposium.objects.all().order_by('dsm_registered_at')
    return render_to_response('matrr/dsm_symposium/symposium_roster.html', {'dsms': dsms}, context_instance=RequestContext(request))


