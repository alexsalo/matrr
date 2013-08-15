import settings, os, math, urllib
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from matrr.models import Request, RequestStatus


def redirect_with_get(url_name, *args, **kwargs):
    url = reverse(url_name, args=args)
    params = urllib.urlencode(kwargs)
    return HttpResponseRedirect(url + "?%s" % params)


def fetch_resources(uri, rel):
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))

    return path


def remove_values_from_list(base_list, removal_list):
    return [value for value in base_list if value not in removal_list]


def sort_tissues_and_add_quantity_css_value(tissue_requests):
    for tissue_request_form in tissue_requests:
        tissue_request = tissue_request_form.instance
        tissue_request.sorted_tissue_request_reviews = sorted(tissue_request.get_reviews(),
                                                              key=lambda x: x.review.user.username)
        for tissue_request_review in tissue_request.sorted_tissue_request_reviews:
            if tissue_request_review.is_finished():
                tissue_request_review.quantity_css_value = int(
                    10 - (math.fabs(5 - tissue_request_review.get_quantity(css=True)) * 2))


def get_or_create_cart(request, cohort):
    # get the user's cart if it already exists
    if Request.objects.cart().filter(user=request.user.id).count():
        cart_request = Request.objects.cart().get(user=request.user.id)
        # check that the cart is for this cohort
        if cart_request.cohort != cohort:
            # take corrective action (display a page that asks the user if they want to abandon their cart and start with this cohort)
            # if the cart is empty, just delete it
            if not cart_request.get_requested_tissue_count():
                cart_request.delete()
                #create a new cart
                cart_request = Request(user=request.user, req_status=RequestStatus.Cart,
                                       cohort=cohort, req_request_date=datetime.now())
                cart_request.save()
            else:
                #the cart was not empty, so give the user the option to delete the cart and continue
                return None
            # it would probably be better to implement this as a custom exception handled with middleware,
            # but for now I will just have this function return None in this case and let the
            # calling function handle the error
    else:
        #create a new cart
        cart_request = Request(user=request.user, req_status=RequestStatus.Cart,
                               cohort=cohort, req_request_date=datetime.now())
        cart_request.save()

    return cart_request


def create_paginator_instance(request, queryset, count):
    if len(queryset) > 0:
        paginator = Paginator(queryset, count)
        # Make sure page request is an int. If not, deliver first page.
        try:
            page = int(request.GET.get('page', '1'))
        except ValueError:
            page = 1
        # If page request (9999) is out of range, deliver last page of results.
        try:
            paged = paginator.page(page)
        except (EmptyPage, InvalidPage):
            paged = paginator.page(paginator.num_pages)
    else:
        paged = queryset
    return paged


def gather_cohort_protein_images(cohort, proteins):
    images = []
    for protein in proteins:
        cpi_image, is_new = CohortProteinImage.objects.get_or_create(protein=protein, cohort=cohort)
        if cpi_image.pk:
            images.append(cpi_image)
    return images


def gather_cohort_hormone_images(cohort, hormones, params):
    images = []
    for hormone in hormones:
        chi_image, is_new = CohortHormoneImage.objects.get_or_create(hormone=hormone, cohort=cohort, parameters=params)
        if chi_image.pk:
            images.append(chi_image)
    return images


