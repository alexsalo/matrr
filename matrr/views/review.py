import re
from django.core.urlresolvers import reverse
from django.forms.models import modelformset_factory
from django.http import Http404
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.template.loader import render_to_string
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from matrr import emails, gizmo
from matrr.forms import ReviewForm, TissueRequestProcessForm, ReviewResponseForm
from matrr.models import Review, RequestStatus, Account, Request, TissueRequest, Acceptance, Monkey

@user_passes_test(lambda u: u.has_perm('matrr.change_review'), login_url='/denied/')
def reviews_list_view(request):
    # get a list of all reviews for the current user
    reviews = Review.objects.filter(user=request.user.id).filter(req_request__req_status=RequestStatus.Submitted)
    finished_reviews = [review for review in reviews if review.is_finished()]
    unfinished_reviews = [review for review in reviews if not review.is_finished()]
    return render_to_response('matrr/review/reviews.html',
                              {'finished_reviews': finished_reviews,
                               'unfinished_reviews': unfinished_reviews,
                               'num_finished': len(finished_reviews),
                               'num_unfinished': len(unfinished_reviews)},
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.change_review'), login_url='/denied/')
def review_detail(request, review_id):
    # get the review
    review = Review.objects.get(rvs_review_id=review_id)
    if review.user != request.user:
        raise Http404('This page does not exist.')
    # get the request being reviewed
    req_request = review.req_request

    if request.method == 'POST':
        if request.POST['submit'] == 'cancel':
            messages.info(request, 'Review cancelled.')
            return redirect(reverse('review-list'))

        form = ReviewForm(data=request.POST.copy(), instance=review)

        if form.is_valid():
            # all the forms are valid, so save the data
            form.save()
            messages.success(request, 'Review saved.')
            return redirect(reverse('review-list'))
    else:
        # create the forms for the review and the tissue request reviews
        form = ReviewForm(instance=review)
    return render_to_response('matrr/review/review_form.html',
                              {'review': review,
                               'req_request': req_request,
                               'form': form,
                              },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_review_overview'), login_url='/denied/')
def review_history_list(request):
    req_requests = Request.objects.evaluated().order_by('-req_modified_date')
    req_requests = req_requests.distinct()

    reviewers = Account.objects.users_with_perm('change_review').order_by('-username')

    paginator = Paginator(req_requests, 20) # Show 25 contacts per page

    if request.GET and 'page' in request.GET:
        page = request.GET.get('page')
    else:
        page = 1

    try:
        verified_requests = paginator.page(page)
    except PageNotAnInteger:
        # If page is not an integer, deliver first page.
        verified_requests = paginator.page(1)
    except EmptyPage:
        # If page is out of range (e.g. 9999), deliver last page of results.
        verified_requests = paginator.page(paginator.num_pages)

    return render_to_response('matrr/review/reviews_history.html',
                              {'req_requests': verified_requests,
                               'reviewers': reviewers,
                              },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_review_overview'), login_url='/denied/')
def review_overview_list(request):
    # get a list of all tissue requests that are submitted, but not accepted or rejected

    req_requests = Request.objects.submitted().order_by('req_request_date')
    # get a list of all reviewers
    overviewers = Account.objects.users_with_perm('change_review')
    for req_request in req_requests:
        req_request.complete = list()
        for reviewer in overviewers:
            for review in req_request.review_set.filter(user=reviewer):
                if review.is_finished():
                    req_request.complete.append("complete")
                else:
                    req_request.complete.append("pending")

    return render_to_response('matrr/review/reviews_overviews.html',
                              {'req_requests': req_requests,
                               'reviewers': overviewers,
                              },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_review_overview'), login_url='/denied/')
def review_overview_price(request, req_request_id):
    req = get_object_or_404(Request, req_request_id=req_request_id)
    accepted_or_partial = False
    PriceFormset = modelformset_factory(TissueRequest, fields=['rtt_estimated_cost'], extra=0)

    for tissue_request in req.get_requested_tissues():
        if tissue_request.get_accepted() != Acceptance.Rejected:
            accepted_or_partial = True

    if not accepted_or_partial:
        for tr in req.tissue_request_set.all():
            tr.rtt_estimated_cost = 0
            tr.save()
        return redirect(reverse('review-overview-process', args=[req_request_id]))

    if request.POST:
        cost_forms = PriceFormset(request.POST)
        if cost_forms.is_valid():
            cost_forms.save()
            return redirect(reverse('review-overview-process', args=[req_request_id]))
        else:
            return render_to_response('matrr/review/review_overview_price.html',
                                      {'req': req, 'forms': cost_forms},
                                      context_instance=RequestContext(request))
    else:
        queryset = req.tissue_request_set.all()
        accepted_queryset = set()
        for tr in queryset:
            if tr.get_accepted() != Acceptance.Rejected:
                accepted_queryset.add(tr.pk)

        quer = TissueRequest.objects.filter(pk__in=accepted_queryset)
        for tr in quer:
            if tr.rtt_estimated_cost is None:
                tr.rtt_estimated_cost = tr.get_estimated_cost()
                tr.save()
        cost_forms = PriceFormset(queryset=quer)
        return render_to_response('matrr/review/review_overview_price.html', {'req': req, 'forms': cost_forms},
                                  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_review_overview'), login_url='/denied/')
def review_overview(request, req_request_id):
    # get the request being reviewed
    req_request = get_object_or_404(Request, pk=req_request_id) # get or 404 ?
    no_monkeys = False

    if req_request.is_evaluated():
        no_monkeys = True
    if 'HTTP_REFERER' in request.META:
        back_url = request.META['HTTP_REFERER']
    else:
        back_url = ""

    for tr in req_request.tissue_request_set.all():
        tr.rtt_estimated_cost = None
        tr.save()
    req_request.save()

    TissueRequestFormSet = modelformset_factory(TissueRequest, form=TissueRequestProcessForm, extra=0)
    if request.POST:
        tissue_request_forms = TissueRequestFormSet(request.POST, prefix='tissue_requests')

        if tissue_request_forms.is_valid():
            tissue_request_forms.save()
            #return redirect(reverse('review-overview-process', args=[req_request_id]))
            # move to price confirmation

            #			req_request.req_estimated_cost = None # discard the manual price, do not use price from previous unsuccessful process attempts
            for tr in req_request.tissue_request_set.all():
                tr.rtt_estimated_cost = None
                tr.save()
            req_request.save()
            return redirect(reverse('review-overview-price', args=[req_request_id]))
        else:
            # get the reviews for the request
            reviews = list(req_request.review_set.all())
            reviews.sort(key=lambda x: x.user.username)

            gizmo.sort_tissues_and_add_quantity_css_value(tissue_request_forms)

            for form in tissue_request_forms:
                form.instance.not_accepted_monkeys = list()
                for monkey in form.instance.monkeys.all():
                    if monkey not in form.instance.accepted_monkeys.all():
                        form.instance.not_accepted_monkeys.append(monkey)

            return render_to_response('matrr/review/review_overview.html',
                                      {'reviews': reviews,
                                       'req_request': req_request,
                                       'tissue_requests': tissue_request_forms,
                                       'back_url': back_url,
                                       'no_monkeys': no_monkeys
                                      },
                                      context_instance=RequestContext(request))

    else:
        # get the tissue requests
        tissue_request_forms = TissueRequestFormSet(queryset=req_request.tissue_request_set.all(),
                                                    prefix='tissue_requests')
        for form in tissue_request_forms:
            form.instance.not_accepted_monkeys = list()
            for monkey in form.instance.monkeys.all():
                if monkey not in form.instance.accepted_monkeys.all():
                    form.instance.not_accepted_monkeys.append(monkey)

        # get the reviews for the request
        reviews = list(req_request.review_set.all())
        reviews.sort(key=lambda x: x.user.username)

        gizmo.sort_tissues_and_add_quantity_css_value(tissue_request_forms)

        return render_to_response('matrr/review/review_overview.html',
                                  {'reviews': reviews,
                                   'req_request': req_request,
                                   'tissue_requests': tissue_request_forms,
                                   'back_url': back_url,
                                   'no_monkeys': no_monkeys
                                  },
                                  context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_review_overview'), login_url='/denied/')
def request_review_process(request, req_request_id):
    # get the tissue request
    req_request = Request.objects.get(req_request_id=req_request_id)

    # check the status
    accepted = False
    partial = False
    for tissue_request in req_request.get_requested_tissues():
        if tissue_request.get_accepted() != Acceptance.Rejected:
            accepted = True
        if tissue_request.get_accepted() != Acceptance.Accepted:
            partial = True
    if accepted and not partial:
        status = RequestStatus.Accepted
        email_template = 'matrr/review/request_accepted_email.txt'
    elif accepted and partial:
        status = RequestStatus.Partially
        email_template = 'matrr/review/request_partially_accepted_email.txt'
    else:
        status = RequestStatus.Rejected
        email_template = 'matrr/review/request_rejected_email.txt'

    if request.POST:
        if request.POST['submit'] == 'Finalize and Send Email':
            # get the submitted form
            form = ReviewResponseForm(data=request.POST, tissue_requests=req_request.get_requested_tissues())
            if form.is_valid():
                # update the unavailable_lists
                for tissue_request in req_request.get_requested_tissues():
                    if tissue_request.get_tissue():
                        tissue = tissue_request.get_tissue()
                        unavailable_list = tissue.unavailable_list.all()
                        monkey_list = tissue_request.monkeys.all()
                        # remove any monkeys in the request from the list
                        unavailable_list = gizmo.remove_values_from_list(unavailable_list, monkey_list)
                        unavailable_list.extend(Monkey.objects.filter(mky_id__in=form.cleaned_data[str(tissue_request)]))
                        tissue.unavailable_list = unavailable_list
                        tissue.save()
                req_request.req_status = status
                req_request.save()
                messages.success(request, "The tissue request has been processed.")
                emails.send_processed_request_email(form.cleaned_data, req_request)
                messages.info(request, str(req_request.user.username) + " was sent an email informing him/her that the request was processed.")
                return redirect(reverse('review-overview-list'))
            else:
                return render_to_response('matrr/review/process.html',
                                          {'form': form,
                                           'req_request': req_request,
                                           'Acceptance': Acceptance},
                                          context_instance=RequestContext(request))
        else:
            messages.info(request, "The tissue request has not been processed.  No email was sent.")
            return redirect(reverse('review-overview-list'))
    else:
        # get the subject
        subject = render_to_string('matrr/review/request_email_subject.txt',
                                   {'status': status, 'cohort': req_request.cohort})
        # Email subject *must not* contain newlines
        subject = ''.join(subject.splitlines())
        request_url = reverse('order-detail', args=[req_request.req_request_id])
        body = render_to_string(email_template,
                                {'request_url': request_url,
                                 'req_request': req_request,
                                 'Acceptance': Acceptance})
        body = re.sub('(\r?\n){2,}', '\n\n', body)
        form = ReviewResponseForm(tissue_requests=req_request.get_requested_tissues(),
                                  initial={'subject': subject, 'body': body})
        return render_to_response('matrr/review/process.html',
                                  {'form': form,
                                   'req_request': req_request,
                                   'Acceptance': Acceptance},
                                  context_instance=RequestContext(request))


