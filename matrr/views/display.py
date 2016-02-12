from datetime import datetime
import json
from django.contrib.auth.decorators import login_required, user_passes_test
from django.core.urlresolvers import reverse
from django.http import Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.core.paginator import Paginator, InvalidPage, EmptyPage
from django.contrib import messages
from django.views.generic import DetailView, ListView
from matrr import gizmo
from matrr.models import Cohort, CohortImage, Monkey, MonkeyImage, TissueType, TissueRequest, TissueCategory, Event
from matrr.forms import TissueRequestForm, DataRequestForm
#from django.views.decorators.cache import cache_page

cohort_timeline = DetailView.as_view(queryset=Cohort.objects.filter(),
                                     context_object_name='cohort',
                                     template_name='matrr/timeline.html')

event_list = ListView.as_view(queryset=Event.objects.filter(date__gte=datetime.now()).order_by('date', 'name'),
                              context_object_name='event_list',
                              template_name='matrr/events.html',
                              paginate_by=10)

archived_event_list = ListView.as_view(queryset=Event.objects.filter(date__lt=datetime.now()).order_by('-date', 'name'),
                                       context_object_name='event_list',
                                       template_name='matrr/archived-events.html',
                                       paginate_by=10)

cohort_publication_list = DetailView.as_view(queryset=Cohort.objects.all(),
                                             context_object_name='cohort',
                                             template_name='matrr/publications.html')




### Handles the display of each cohort and the lists of cohorts
#@cache_page(60 * 60)
def cohorts_view_available(request):
    cohorts = Cohort.objects.nicotine_filter(request.user).filter(coh_upcoming=False).order_by('coh_cohort_name')
    template_name = 'matrr/available_cohorts.html'
    return __cohorts_view(request, cohorts, template_name)

#@cache_page(60 * 60)
def cohorts_view_upcoming(request):
    cohorts = Cohort.objects.nicotine_filter(request.user).filter(coh_upcoming=True).order_by('coh_cohort_name')
    template_name = 'matrr/upcoming_cohorts.html'
    return __cohorts_view(request, cohorts, template_name)

#@cache_page(60 * 60)
def cohorts_view_all(request):
    cohorts = Cohort.objects.nicotine_filter(request.user).order_by('coh_cohort_name')
    template_name = 'matrr/cohorts.html'
    return __cohorts_view(request, cohorts, template_name)

#@cache_page(60 * 60)
def cohorts_view_assay(request):
    return redirect(reverse('tissue-shop-landing', args=[Cohort.objects.get(coh_cohort_name__iexact="Assay Development").pk, ]))


def __set_images(cohort, user):
    cohort.images = cohort.image_set.filter(canonical=True).vip_filter(user)
    return cohort


def __cohorts_view(request, cohorts, template_name):
    cohorts_all = Cohort.objects.nicotine_filter(request.user).order_by('coh_cohort_name')
    cohorts = [__set_images(cohort, request.user) for cohort in cohorts]
    # coh_ids = [c.coh_cohort_id for c in cohorts]
    # coh_names = [c.coh_cohort_name for c in cohorts]

    ## Paginator stuff
    if len(cohorts) > 0:
        paginator = Paginator(cohorts, 10)
        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        # If page request (9999) is out of range, deliver last page of results.
        try:
            cohort_list = paginator.page(page)
        except (EmptyPage, InvalidPage):
            cohort_list = paginator.page(paginator.num_pages)
    else:
        cohort_list = cohorts
    return render_to_response(template_name, {'cohort_list': cohort_list, 'cohorts_all' : cohorts_all}, context_instance=RequestContext(request))

#@cache_page(60 * 60 * 24)
def cohort_details(request, **kwargs):
    # Handle the displaying of cohort details
    if kwargs.has_key('pk'):
        cohort = get_object_or_404(Cohort, pk=kwargs['pk'])
        coh_data = True if cohort.cod_set.all().count() else False
        images = CohortImage.objects.filter(cohort=cohort, canonical=True).vip_filter(request.user)
    else:
        return redirect(reverse('cohorts'))
    order_by = request.GET.get('order_by', 'pk')
    monkeys = cohort.monkey_set.all().order_by(order_by)

    from matrr.models import NecropsySummary
    necropsy_summary = NecropsySummary.objects.filter(monkey__in=monkeys)

    has_categories = any(cohort.monkey_set.all().values_list('mky_drinking_category', flat=True))
    return render_to_response('matrr/cohort.html',
                              {'cohort': cohort, 'images': images, 'coh_data': coh_data,
                               'necropsy_summary': necropsy_summary,
                               'plot_gallery': True, 'has_categories': has_categories, 'monkeys': monkeys},
                              context_instance=RequestContext(request))


### Clear cache is MTDS or BECs changed, using signals
# from django.db.models.signals import post_save
# from django.core.cache import cache
# from matrr.models import MonkeyToDrinkingExperiment, MonkeyBEC
# def MTDS_changed(sender, **kwargs):
#     cache.clear()
# post_save.connect(MTDS_changed, sender=MonkeyToDrinkingExperiment)
# post_save.connect(MTDS_changed, sender=MonkeyBEC)
# post_save.connect(MTDS_changed, sender=MonkeyImage)
# post_save.connect(MTDS_changed, sender=CohortImage)

def __monkey_detail(request, mky_id, coh_id=0):
    try:
        monkey = Monkey.objects.get(mky_id=mky_id)
    except:
        raise Http404(u"No %(verbose_name)s found matching the query" %
                      {'verbose_name': Monkey._meta.verbose_name})

    if coh_id and str(monkey.cohort.coh_cohort_id) != coh_id:
        raise Http404(u"No %(verbose_name)s found matching the query" %
                      {'verbose_name': Monkey._meta.verbose_name})

    images = MonkeyImage.objects.filter(monkey=monkey, canonical=True).vip_filter(request.user).order_by('method')
    return render_to_response('matrr/monkey.html', {'monkey': monkey, 'images': images, 'plot_gallery': True},
                              context_instance=RequestContext(request))


def monkey_cohort_detail_view(request, coh_id, mky_id):
    return __monkey_detail(request, mky_id, coh_id=coh_id)


def monkey_detail_view(request, mky_id):
    return __monkey_detail(request, mky_id)


def tissue_shop_detail_view(request, coh_id, tissue_id):
    current_cohort = Cohort.objects.get(coh_cohort_id=coh_id)
    cart_request = gizmo.get_or_create_cart(request, current_cohort)
    if cart_request is None:
        # The user has a cart open with a different cohort
        # display a page that gives the user the option to delete
        # the existing cart and proceed or to go to the existing cart.
        return render_to_response('matrr/cart/cart_delete_or_keep.html',
                                  {'cohort': current_cohort},
                                  context_instance=RequestContext(request))

    # if we got here, then a request is made with this user and cohort and the status is 'cart'

    # get the current tissue
    current_tissue = TissueType.objects.get(tst_type_id=tissue_id)
    # Shuffle it off to the data_shop view if the user is requesting data
    if current_tissue.category.cat_name == "Data":
        return data_shop_detail_view(request, current_cohort, current_tissue, cart_request)

    # kathy has a special disclaimer for plasma requests.
    if current_tissue.tst_tissue_name == "Plasma":
        messages.info(request, "The policy for blood samples is not the same as most of the other tissues.")
        messages.info(request,
                      """
                      You will need to contact Kathy Grant directly (grantka@ohsu.edu) due to the
                      many NIH supported projects currently underway using these samples.
                      Nevertheless, each of these projects will begin posting the data (such as
                      protein and hormone data).  Helping labs with in silico hypothesis testing
                      is a future aim of the MATRR.
                      """)

    instance = TissueRequest(tissue_type=current_tissue, req_request=cart_request)

    # Upcoming cohort warning
    if current_cohort.coh_upcoming:
        import datetime
        today = datetime.date.today()
        warning_message = "Warning:  Because this cohort has not yet gone to necropsy, we cannot guarantee all tissue from all monkeys will be available for request, due to uncontrollable events (illness, accidental death, etc).  If a requested tissue was approved but is not available after necropsy the user will be notified and the request and its cost will be corrected.  Thank you for your understanding regarding this uncertainty."
        try:
            necropsy_date = current_cohort.cohort_event_set.filter(event__evt_name="Necropsy Start")[0].cev_date
            days_to_necropsy = (necropsy_date - today).days
        except IndexError: # IndexError if no cohort events exist
            messages.warning(request, warning_message)
        except TypeError: # TypeError if cev_date == None
            messages.warning(request, warning_message)
        else:
            if days_to_necropsy >= 6 * 60:
                messages.warning(request, warning_message)

    if request.method != 'POST':
        # now we need to create the form for the tissue type
        tissue_request_form = TissueRequestForm(req_request=cart_request, tissue=current_tissue, instance=instance,
                                                initial={'monkeys': current_cohort.monkey_set.all()})
        # create the response
        tissue_request_form.visible_fields()
    else:
        data = request.POST.copy()
        tissue_request_form = TissueRequestForm(data=data,
                                                req_request=cart_request,
                                                tissue=current_tissue,
                                                instance=instance)
        if tissue_request_form.is_valid():
            url = reverse('tissue-shop-landing', args=[cart_request.cohort.coh_cohort_id, ])
            try:
                tissue_request_form.save()
            except Exception as e:
                print e
                messages.error(request,
                               'Error adding tissue to cart.  Possible duplicate tissue request already in cart.')
                return redirect(url)

            messages.success(request, 'Item added to cart')
            return redirect(url)
    return render_to_response('matrr/tissue_shopping.html', {'form': tissue_request_form,
                                                             'cohort': current_cohort,
                                                             'page_title': current_tissue.tst_tissue_name},
                              context_instance=RequestContext(request))


def data_shop_detail_view(request, current_cohort, current_tissue, cart_request):
    tissue_request = TissueRequest(tissue_type=current_tissue, req_request=cart_request)
    bogus_initial_data = {'rtt_fix_type': 'data',
                          'rtt_amount': 1,
                          'rtt_prep_type': 'data',
                          'rtt_units': 'whole'}
    if request.method != 'POST':
        # first, give them the disclaimer.
        messages.info(request, "The availability and policy of MATRR data is not the same as the tissues.")
        messages.info(request,
                      """
                      The MATRR site is a user-driven service and the data availability is thus limited to users' prior research AND the submission
                      of researchers' data back into the MATRR after publication.  All users who receive tissues through MATRR have agreed to submit
                      their data to us for distribution to other users like you.  As a results, only data submitted to the MATRR repository is
                      available for dissemination.  In addition, a core concern of the MATRR is the appropriate ascription of prior researchers' work
                      and citation of their publication.  A faithful engagement of this concern will be required to receive data.
                      """)
        messages.warning(request,
                         """
                         All data requests must include date ranges being requested.  Please look at the cohort's timeline and include
                         specific date ranges of interest.
                         """)
        # now we need to create the form for the tissue type
        data_request_form = DataRequestForm(req_request=cart_request,
                                              tissue=current_tissue,
                                              instance=tissue_request,
                                              initial={'monkeys': current_cohort.monkey_set.all(),})
        # create the response
        data_request_form.visible_fields()
    else:
        data = request.POST.copy()
        data.update(bogus_initial_data)
        data_request_form = DataRequestForm(data=data,
                                              req_request=cart_request,
                                              tissue=current_tissue,
                                              instance=tissue_request)
        if data_request_form.is_valid():
            url = reverse('tissue-shop-landing', args=[cart_request.cohort.coh_cohort_id, ])
            try:
                data_request_form.save()
            except Exception as e:
                messages.error(request,
                               'Error adding data to cart.  Possible duplicate data request already in cart.')
                return redirect(url)

            messages.success(request, 'Item added to cart')
            return redirect(url)
    return render_to_response('matrr/data_shopping.html', {'form': data_request_form,
                                                           'cohort': current_cohort,
                                                           'page_title': current_tissue.tst_tissue_name},
                              context_instance=RequestContext(request))


def tissue_shop_landing_view(request, coh_id):
    context = dict()
    assay = Cohort.objects.get(coh_cohort_name__iexact="Assay Development")
    cohort = Cohort.objects.get(coh_cohort_id=coh_id)
    context['cohort'] = cohort
    if cohort != assay:
        context['assay'] = assay
    categories = list(TissueCategory.objects.order_by('cat_name').all())
    if TissueCategory.objects.filter(cat_name='Custom'):
        custom = TissueCategory.objects.get(cat_name='Custom')
        categories.remove(custom)
        categories.append(custom)
    if TissueCategory.objects.filter(cat_name='Data'):
        data = TissueCategory.objects.get(cat_name='Data')
        categories.remove(data)
        categories.append(data)

    context['categories'] = categories
    context['cohort'] = cohort
    if cohort != assay:
        context['assay'] = assay
    return render_to_response('matrr/tissue_shopping_landing.html', context, context_instance=RequestContext(request))


def tissue_list(request, tissue_category=None, coh_id=None):
    cohort = None
    if coh_id is not None:
        cohort = Cohort.objects.get(coh_cohort_id=coh_id)
    if tissue_category == "Custom":
        # This breaks the URL scheme # todo: does it?  Fix it?
        return tissue_shop_detail_view(request, cohort.coh_cohort_id,
                                       TissueType.objects.get(tst_tissue_name="Custom").tst_type_id)
    elif tissue_category:
        tissue_list = TissueType.objects.filter(category__cat_name=tissue_category).order_by('tst_tissue_name')
    else:
        tissue_list = TissueType.objects.order_by('tst_tissue_name')

    available = list()
    unavailable = list()

    for tissue in tissue_list:
        if tissue.get_cohort_availability(cohort):
            available.append(tissue)
        else:
            unavailable.append(tissue)
    return render_to_response('matrr/tissues.html', {'tissues': available,
                                                     'tissues_unavailable': unavailable,
                                                     'title': tissue_category,
                                                     'cohort': cohort,
                                                     'plot_gallery': True, },
                              context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.data_repository_grid'), login_url='/denied/')
def data_repository_grid(request):
    """
    To update, run:
    matrr.utils.database.dump.dump_MATRR_current_data_grid(dump_json=True, dump_csv=False)
    """
    if request.method == 'POST':
        if 'refresh_data' in request.POST:
            import thread
            from matrr.utils.database import dump
            thread.start_new_thread(dump.dump_MATRR_current_data_grid, (), {'dump_json':True, "dump_csv": False})
            messages.success(request, "A background thread was started that will update the JSON file this table reads.")
    try:
        json_file = open('matrr/utils/DATA/json/current_data_grid.json', 'r')
    except IOError:
        messages.error(request, "MATRR could not find the information needed for this page.  If this problem persists please notify a MATRR admin.")
        context = {}
    else:
        context = json.loads(json_file.read())
    return render_to_response('matrr/data_repository_grid.html', context, context_instance=RequestContext(request))

@user_passes_test(lambda u: u.has_perm('matrr.data_repository_grid'), login_url='/denied/')
def monkey_hormone_challenge_data_grid(request):
    from matrr.models import Cohort, MonkeyHormoneChallenge, PharmalogicalChallengeChoice, MonkeyHormoneChoice
    cohorts = MonkeyHormoneChallenge.objects.all().values_list('monkey__cohort__coh_cohort_id', 'monkey__cohort__coh_cohort_name').distinct()

    cohorts_mhc = []
    for cohort in cohorts:
        coh_mhc = {}
        for ep in [1, 2, 3, 4, 5, 6, 7, 8]:
            ep_hormone = {}
            cohort_has_this_ep = False
            for hormone in ['mhc_doc', 'mhc_ald', 'mhc_vas', 'mhc_acth', 'mhc_gh', 'mhc_estra', 'mhc_cort', 'mhc_dheas', 'mhc_test']:
                hormone_verbose = MonkeyHormoneChallenge._meta.get_field_by_name(hormone)[0].verbose_name
                challenges = MonkeyHormoneChallenge.objects.filter(monkey__cohort__coh_cohort_id=cohort[0])\
                    .filter(**{hormone + '__isnull': False}).filter(mhc_ep=ep).\
                    values_list('mhc_challenge', flat=True).distinct()
                ep_hormone[hormone_verbose] = challenges
                if len(challenges) > 0:
                    cohort_has_this_ep = True
            if cohort_has_this_ep:
                coh_mhc[ep] = ep_hormone
        cohorts_mhc.append((cohort, coh_mhc))
    return render_to_response('matrr/data_grid_monkey_hormone_challenge.html',
                              {'cohorts_mhc': cohorts_mhc,
                               'challenges': PharmalogicalChallengeChoice,
                               'hormones': [c[1] for c in MonkeyHormoneChoice],
                               'n_rows_challenge': len(PharmalogicalChallengeChoice) + 1},
                              context_instance=RequestContext(request))

@login_required
def drinking_category_definition(request):
    context = {}
    return render_to_response('matrr/drinking_category_definition.html', context, context_instance=RequestContext(request))
