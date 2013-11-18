import os
import mimetypes
from datetime import datetime
from django.forms.models import formset_factory
from django.http import HttpResponse, HttpResponseRedirect
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from registration.backends.default import views
from djangosphinx.models import SphinxQuerySet
from registration.models import RegistrationProfile
from matrr.settings import MEDIA_ROOT, STATIC_URL
from matrr import emails, gizmo
from matrr.forms import MatrrRegistrationForm, ContactUsForm, FulltextSearchForm, MTAValidationForm, AdvancedSearchSelectForm, AdvancedSearchFilterForm, PublicationCohortSelectForm
from matrr.models import * # sendfile() uses a lot of models

def matrr_handler500(request):
    from django.core.context_processors import static
    return render_to_response('500.html', static(request), context_instance=RequestContext(request))

def matrr_handler403(request, reason=''):
    from django.core.context_processors import static
    return render_to_response('403.html', static(request), context_instance=RequestContext(request))

def index_view(request):
    index_context = {'event_list': Event.objects.filter(date__gte=datetime.now()).order_by('date', 'name')[:5],
                     'pub_list': Publication.objects.all().exclude(published_year=None).order_by('-published_year', '-published_month')[:2],
                     'search_form': FulltextSearchForm(),
                     'plot_gallery': True,
    }

    return render_to_response('matrr/index.html', index_context, context_instance=RequestContext(request))



#def registration(request):
#    from registration.views import register
#    return register(request, form_class=MatrrRegistrationForm)

class RegistrationView(views.RegistrationView):
    disallowed_url = 'matrr-home'
    form_class = MatrrRegistrationForm
    success_url = 'registration_complete'
    template_name = 'registration/registration_form.html'

    def registration_allowed(self, request):
        return True

    def register(self, request, **cleaned_data):
        user = RegistrationProfile.objects.create_inactive_user(username=cleaned_data['username'],
                                                                password=cleaned_data['password1'],
                                                                email=cleaned_data['email'],
                                                                site=settings.SITE_ID)
        user.last_name = cleaned_data['last_name']
        user.first_name = cleaned_data['first_name']
        user.save()
        account = Account(user=user)
        account.institution = cleaned_data['institution']
        account.phone_number = cleaned_data['phone_number']
        account.act_real_address1 = cleaned_data['act_real_address1']
        account.act_real_address2 = cleaned_data['act_real_address2']
        account.act_real_city = cleaned_data['act_real_city']
        account.act_real_state = cleaned_data['act_real_state']
        account.act_real_zip = cleaned_data['act_real_zip']
        account.act_real_country = cleaned_data['act_real_country']
        account.act_address1 = account.act_real_address1
        account.act_address2 = account.act_real_address2
        account.act_city = account.act_real_city
        account.act_country = account.act_real_country
        account.act_state = account.act_real_state
        account.act_zip = account.act_real_zip
        account.act_shipping_name = user.first_name + " " + user.last_name
        account.save()

        from matrr.emails import send_verify_new_account_email
        send_verify_new_account_email(account)
        return user



def logout(request, next_page=None):
    from django.contrib.auth import logout as auth_logout
    auth_logout(request)
    return HttpResponseRedirect(next_page or "/")


### Handles all non-dynamic pages.
def pages_view(request, static_page):
    # The issue I was having with file.open('/path/to/text.txt', r) was the inconsistent directory structure between
    # the dev and production environments (laptop vs gleek).  I'm certain there is a combination of settings that would
    # handle that more beautifully, but for the scope of 3 files I've wasted enough time.
    # it didnt stay 3 pages for long....

    template = 'matrr/pages/' + static_page + ".html"
    return render_to_response(template, {}, context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.verify_mta'), login_url='/denied/')
def mta_list(request):
    MTAValidationFormSet = formset_factory(MTAValidationForm, extra=0)
    if request.method == "POST":
        formset = MTAValidationFormSet(request.POST)
        if formset.is_valid():
            for mtaform in formset:
                data = mtaform.cleaned_data
                mta = Mta.objects.get(pk=data['primarykey'])
                if data['is_valid'] != mta.mta_is_valid:
                    mta.mta_is_valid = data['is_valid']
                    mta.save()
            messages.success(request, message="This page of MTAs has been successfully updated.")
        else:
            messages.error(request, formset.errors)

    all_mta = Mta.objects.all().order_by('user', 'pk')
    paginator = Paginator(all_mta, 15)

    if request.GET and 'page' in request.GET:
        page = request.GET.get('page')
    else:
        page = 1
    try:
        mta_list = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        mta_list = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        mta_list = paginator.page(paginator.num_pages)

    initial = []
    for mta in mta_list.object_list:
        mta_initial = {'is_valid': mta.mta_is_valid, 'username': mta.user.username, 'title': mta.mta_title,
                       'url': mta.mta_file.url, 'primarykey': mta.pk}
        initial.append(mta_initial)

    formset = MTAValidationFormSet(initial=initial)
    return render_to_response('matrr/mta_list.html', {'formset': formset, 'mta_list': mta_list},
                              context_instance=RequestContext(request))


def contact_us(request):
    if request.POST:
        if request.POST['submit'] == 'Send Message':
            # get the submitted form
            form = ContactUsForm(data=request.POST)
            if form.is_valid():
                emails.send_contact_us_email(form.cleaned_data, request.user)
                messages.success(request, "Your message was sent to the MATRR team. You may expect a response shortly.")
                return redirect('/')
            else:
                return render_to_response('matrr/contact_us.html',
                                          {'form': form},
                                          context_instance=RequestContext(request))
        else:
            messages.info(request, "No message has been sent.")
            return redirect('/')
    else:
        try:
            account_info = Account.objects.get(user__id=request.user.id)
            user_email = account_info.user.email
            form = ContactUsForm(initial={'email_from': user_email})
        except Account.DoesNotExist:
            form = ContactUsForm()

        return render_to_response('matrr/contact_us.html',
                                  {'form': form},
                                  context_instance=RequestContext(request))


def search_index(terms, index, model):
    search = SphinxQuerySet(
        index=index,
        mode='SPH_MATCH_EXTENDED2',
        rankmode='SPH_RANK_NONE')

    results = search.query(terms)
    final_results = list()

    for result in results:
        final_results.append(model.objects.get(pk=result['id']))

    return final_results


def search(request):
    form = FulltextSearchForm()
    num_results = 0
    monkey_auth = False

    terms = ''
    results = dict()
    if request.method == 'POST':
        form = FulltextSearchForm(request.POST)
        if form.is_valid():
            terms = form.cleaned_data['terms']

            from django.db.models.loading import get_model
            from matrr.settings import PRIVATE_SEARCH_INDEXES, PUBLIC_SEARCH_INDEXES

            SEARCH_INDEXES = PUBLIC_SEARCH_INDEXES

            for key, value in PRIVATE_SEARCH_INDEXES.items():
                if 'monkey_auth' in key and request.user.has_perm('matrr.monkey_view_confidential'):
                    monkey_auth = True
                    SEARCH_INDEXES['monkey'] = value
                #					results['monkeys'] = search_index(terms, SEARCH_INDEXES[key], Monkey)

            for key, value in SEARCH_INDEXES.items():
                results[key] = search_index(terms, value[0], get_model('matrr', value[1]))

            num_results = 0
            for key in results:
                num_results += len(results[key])

    return render_to_response('matrr/search.html',
                              {'terms': terms,
                               'results': results,
                               'num_results': num_results,
                               'monkey_auth': monkey_auth,
                               'form': form},
                              context_instance=RequestContext(request))


def advanced_search(request):
    monkey_auth = request.user.has_perm('matrr.monkey_view_confidential')
    select_form = AdvancedSearchSelectForm(prefix='select')
    filter_form = AdvancedSearchFilterForm(prefix='filter')

    #	results = Monkey.objects.all().order_by('cohort__coh_cohort_name', 'pk')
    #	mpns = MonkeyProtein.objects.filter(monkey__in=results).exclude(mpn_stdev__lt=1)
    #	for mky in results:
    #		mky.mpns =  mpns.filter(monkey=mky).values_list('protein__pro_abbrev', flat=True).distinct()

    return render_to_response('matrr/advanced_search.html',
                              {'monkeys': Monkey.objects.all(),
                               'monkey_auth': monkey_auth,
                               'select_form': select_form,
                               'filter_form': filter_form,
                               'cohorts': Cohort.objects.nicotine_filter(request.user)},
                              context_instance=RequestContext(request))


def publications(request):
    cohorts = Cohort.objects.exclude(publication_set=None)
    subject = PublicationCohortSelectForm(queryset=cohorts)
    pubs = Publication.objects.all().order_by('-published_year', '-published_month')
    #	session = getattr(request, 'session', '')
    if request.session and request.session.has_key('old_post') and not request.GET:
        request.session.pop('old_post')
    if request.POST or request.session.has_key('old_post'):
        if request.POST:
            post = request.POST
            request.GET = {}
        else:
            post = request.session.pop('old_post')
        subject = PublicationCohortSelectForm(queryset=cohorts, data=post)
        if subject.is_valid():
            request.session['old_post'] = post
            cohorts = subject.cleaned_data['subject']
            if cohorts:
                pubs = Publication.objects.filter(cohorts__in=cohorts).distinct().order_by('-published_year', '-published_month')
        else:
            # The invalid form, of only checkboxes, is assumed invalid because it is blank.
            # Blank forms, when submitted, should display cohort-less publications.
            pubs = Publication.objects.filter(cohorts=None).order_by('-published_year', '-published_month')
            request.session['old_post'] = post
    if pubs.count() > 15:
        page_obj = gizmo.create_paginator_instance(request=request, queryset=pubs, count=15)
        pubs = page_obj.object_list
    else:
        page_obj = None
    return render_to_response('matrr/all_publications.html',
                              {'publications': pubs, 'page_obj': page_obj, 'subject_select_form': subject},
                              context_instance=RequestContext(request))


# Permission-restricted media file hosting
def sendfile(request, pk):
    files = list()

    #	append all possible files
    r = Request.objects.filter(req_experimental_plan=pk)
    files.append((r, 'req_experimental_plan'))
    r = Mta.objects.filter(mta_file=pk)
    files.append((r, 'mta_file'))
    r = ResearchUpdate.objects.filter(rud_file=pk)
    files.append((r, 'rud_file'))
    r = CohortData.objects.filter(cod_file=pk)
    files.append((r, 'cod_file'))
    r = MonkeyImage.objects.filter(thumbnail=pk)
    files.append((r, 'thumbnail'))
    r = MonkeyImage.objects.filter(svg_image=pk)
    files.append((r, 'svg_image'))
    r = MonkeyImage.objects.filter(image=pk)
    files.append((r, 'image'))
    r = MonkeyImage.objects.filter(html_fragment=pk)
    files.append((r, 'html_fragment'))
    r = CohortImage.objects.filter(thumbnail=pk)
    files.append((r, 'thumbnail'))
    r = CohortImage.objects.filter(image=pk)
    files.append((r, 'image'))
    r = CohortImage.objects.filter(html_fragment=pk)
    files.append((r, 'html_fragment'))
    r = CohortImage.objects.filter(svg_image=pk)
    files.append((r, 'svg_image'))
    r = MTDImage.objects.filter(thumbnail=pk)
    files.append((r, 'thumbnail'))
    r = MTDImage.objects.filter(image=pk)
    files.append((r, 'image'))
    r = MTDImage.objects.filter(html_fragment=pk)
    files.append((r, 'html_fragment'))
    r = MTDImage.objects.filter(svg_image=pk)
    files.append((r, 'svg_image'))
    r = DataFile.objects.filter(dat_data_file=pk)
    files.append((r, 'dat_data_file'))
    r = CohortProteinImage.objects.filter(image=pk)
    files.append((r, 'image'))
    r = CohortProteinImage.objects.filter(thumbnail=pk)
    files.append((r, 'thumbnail'))
    r = CohortProteinImage.objects.filter(svg_image=pk)
    files.append((r, 'svg_image'))
    r = MonkeyProteinImage.objects.filter(image=pk)
    files.append((r, 'image'))
    r = MonkeyProteinImage.objects.filter(thumbnail=pk)
    files.append((r, 'thumbnail'))
    r = MonkeyProteinImage.objects.filter(svg_image=pk)
    files.append((r, 'svg_image'))
    r = CohortHormoneImage.objects.filter(image=pk)
    files.append((r, 'image'))
    r = CohortHormoneImage.objects.filter(thumbnail=pk)
    files.append((r, 'thumbnail'))
    r = CohortHormoneImage.objects.filter(svg_image=pk)
    files.append((r, 'svg_image'))
    r = MonkeyHormoneImage.objects.filter(image=pk)
    files.append((r, 'image'))
    r = MonkeyHormoneImage.objects.filter(thumbnail=pk)
    files.append((r, 'thumbnail'))
    r = MonkeyHormoneImage.objects.filter(svg_image=pk)
    files.append((r, 'svg_image'))

    #	this will work for all listed files
    _file = None
    for r, f in files:
        if len(r) > 0:
            if r[0].verify_user_access_to_file(request.user):
                _file = getattr(r[0], f)
            break
    if not _file:
        return HttpResponseRedirect(STATIC_URL + 'images/permission_denied.jpg')

    if _file.url.count('/media') > 0:
        file_url = _file.url.replace('/media/', '')
    else:
        file_url = _file.url.replace('/', '', 1)

    response = HttpResponse()
    response['X-Sendfile'] = os.path.join(MEDIA_ROOT, file_url)

    content_type, encoding = mimetypes.guess_type(file_url)
    if not content_type:
        content_type = 'application/octet-stream'
    response['Content-Type'] = content_type
    response['Content-Disposition'] = 'attachment; filename="%s"' % os.path.basename(file_url)
    return response
