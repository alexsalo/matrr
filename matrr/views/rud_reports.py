from matrr import settings
from django.core.files import File
from django.core.urlresolvers import reverse
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from matrr.decorators import user_owner_test
from matrr.forms import RudUpdateForm, RudProgressForm
from matrr.models import ResearchUpdate, ResearchProgress, Request

def rud_update(request):
    if request.method == 'POST':
        form = RudUpdateForm(user=request.user.pk, data=request.POST)
        if form.is_valid():
            cd = form.cleaned_data
            if cd['progress'] == ResearchProgress.Complete:
                cd['req_request'] = [req.pk for req in cd['req_request']] # This is crucial.  Read below
                # Okok so I without this line, in django 1.5 the queryset that the RudUpdateForm.req_request creates wasn't getting
                # JSON serialized inside the session/forward/etc.  It was kind of a pain in the ass to track down, haven't had that
                # trouble in a while.
                request.session['rud_form'] = cd
                return redirect(reverse('rud-complete'))
            elif cd['progress'] == ResearchProgress.InProgress:
                cd['req_request'] = [req.pk for req in cd['req_request']]
                request.session['rud_form'] = cd
                try:
                    return redirect('rud-in-progress')
                except:
                    pass
                try:
                    return redirect(reverse('rud-in-progress'))
                except:
                    raise Exception()
            else: # ResearchUpdate.NoProgress
                for req in cd['req_request']:
                    rud = ResearchUpdate()
                    rud.req_request = req
                    rud.rud_progress = cd['progress']
                    rud.save()
                messages.info(request, "You will be emailed again in %d days to provide another research update." % settings.ResearchUpdateNoProgressGrace)
                return redirect(reverse('account-view'))
    else:
        form = RudUpdateForm(user=request.user.pk)
    request.session['rud_form'] = None
    return render_to_response('matrr/rud_reports/rud_update.html', {'form': form, }, context_instance=RequestContext(request))


def rud_progress(request):
    progress_form = ''
    rud_update_data = request.session.get('rud_form', '')
    update_form = RudUpdateForm(user=request.user.pk, data=rud_update_data)
    assert update_form.is_valid(), "This form must be valid when passed POST data via session cache."
    if not update_form:
        messages.error(request, "There was an issue loading the first part of your research update, please start over.  If this continues to happen, please contact a MATRR administrator.")
        return redirect(reverse('rud-upload'))

    update_cd = update_form.cleaned_data
    progress = update_cd['progress']
    if request.method == 'POST':
        post = request.POST.copy()
        post.update({'progress': progress})
        progress_form = RudProgressForm(post, request.FILES)
        if progress_form.is_valid():
            progress_form.clean()
            if not progress_form.errors:
                update_cd = update_form.cleaned_data
                progress_cd = progress_form.cleaned_data
                for req in update_cd['req_request']:
                    rud = ResearchUpdate()
                    rud.req_request = req
                    rud.rud_progress = update_cd['progress']
                    rud.rud_pmid = progress_cd['pmid']
                    rud.rud_file = File(progress_cd['update_file'])
                    rud.rud_comments = progress_cd['comments']
                    rud.rud_data_available = progress_cd['data_available']
                    rud.rud_grant = progress_cd['grants']
                    rud.save()
                messages.success(request, "Your research update was successfully submitted.  Thank you.")
                if update_cd['progress'] == ResearchProgress.NoProgress:
                    grace_period = settings.ResearchUpdateNoProgressGrace
                elif update_cd['progress'] == ResearchProgress.InProgress:
                    grace_period = settings.ResearchUpdateInProgressGrace
                else: # ResearchProgress.Complete
                    grace_period = 0
                if grace_period:
                    messages.info(request, "You will be emailed again in %d days to provide another research update." % grace_period)
                return redirect(reverse('account-view'))

    form = progress_form if progress_form else RudProgressForm(initial={'progress': update_cd['progress']})
    if progress == ResearchProgress.InProgress:
        template = 'matrr/rud_reports/rud_in_progress.html'
    elif progress == ResearchProgress.Complete:
        template = 'matrr/rud_reports/rud_complete.html'
    else:
        messages.error(request,
                       "There was an issue determining the progress of your research update, please start over.  If this continues to happen, please contact a MATRR administrator.")
        return redirect(reverse('rud-upload'))
    return render_to_response(template, {'form': form, }, context_instance=RequestContext(request))


@user_owner_test(lambda u, rud_id: u.has_perm('matrr.view_rud_detail') or get_object_or_404(ResearchUpdate, pk=rud_id).req_request.user == u, 'rud_id')
def rud_detail(request, rud_id):
    rud = get_object_or_404(ResearchUpdate, pk=rud_id)
    return render_to_response('matrr/rud_reports/rud_detail.html', {'rud': rud}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_rud_detail'), login_url='/denied/')
def rud_list(request):
    pending_ruds = ResearchUpdate.objects.all().order_by('req_request', 'rud_date')
    paginator = Paginator(pending_ruds, 20)

    if request.GET and 'page' in request.GET:
        page = request.GET.get('page')
    else:
        page = 1
    try:
        rud_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        rud_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        rud_list = paginator.page(paginator.num_pages)
    return render_to_response('matrr/rud_reports/rud_list.html', {'rud_list': rud_list}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_rud_detail'), login_url='/denied/')
def rud_overdue(request):
    pending_ruds = list()
    for req in Request.objects.shipped().order_by('req_request_date'):
        if req.is_rud_overdue():
            pending_ruds.append(req)
    paginator = Paginator(pending_ruds, 20)

    if request.GET and 'page' in request.GET:
        page = request.GET.get('page')
    else:
        page = 1
    try:
        req_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        req_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        req_list = paginator.page(paginator.num_pages)
    return render_to_response('matrr/rud_reports/req_list.html', {'req_list': req_list}, context_instance=RequestContext(request))


