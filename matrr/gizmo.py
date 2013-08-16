import settings, os, math, urllib, StringIO
from datetime import datetime
from django.core.paginator import Paginator, EmptyPage, InvalidPage
from django.core.urlresolvers import reverse
from django.http import HttpResponseRedirect
from matrr.models import Request, RequestStatus
from django.template import loader, Context
from ho import pisa


def redirect_with_get(url_name, *args, **kwargs):
    """
    Does as the same suggests.  This will redirect the user to the given url_name (from urls.py) with any GET attributes.

    Arguments:  // I didn't write this, but this is how it looks to me -jf
        url_name:  the name= of a url pattern match found in a urls.py file.  Eg: 'cohort-timeline' from matrr/urls.py
        *args: these are passed to django's reverse() when converting url_name into a bona fide url.  Eg: args=[6] would become '/cohort/6/timeline'
        **kwargs:  These are the GET attributes being appended to the url.  Eg:  {monkeys:'10025-10016'} would become "?monkeys=10025-10016'

        Full example:
        url_name='cohort-timeline'
        args = [6]
        kwargs = {monkeys:'10025-10016'}

        Resulting url: /cohort/6/timeline?monkeys=10025-10016
    """
    url = reverse(url_name, args=args)
    params = urllib.urlencode(kwargs)
    return HttpResponseRedirect(url + "?%s" % params)

def fetch_resources(uri, rel):
    """
    I didn't write this either.  It's used by matrr.views.tools.create_pdf_fragment() when creating a PDF from the template.

    Near as I can tell, it replaces the "/media/" and "/static/" in the url (for like images and CSS and such) with the os path to these files on
    the filesystem.

    I have no idea what rel would be used for.  I'm pretty sure the argument is expected to exist even if it isn't use.
    This function is used as a link_callback by the pisa library, and the library probably expects the callback function to accept 2 arguments.
    """
    if uri.startswith(settings.MEDIA_URL):
        path = os.path.join(settings.MEDIA_ROOT, uri.replace(settings.MEDIA_URL, ""))
    elif uri.startswith(settings.STATIC_URL):
        path = os.path.join(settings.STATIC_ROOT, uri.replace(settings.STATIC_URL, ""))

    return path

# todo: remove this method, along with the deprecated inventory system of which it is a part.
def remove_values_from_list(base_list, removal_list):
    """
    This function will remove values from base_list if these values exist in removal_list.  It's only used once in the project,
    and I'm pretty sure it's part of a deprecated inventory functionality.  I haven't gotten around to removing it, but I will.
    """
    return [value for value in base_list if value not in removal_list]

def sort_tissues_and_add_quantity_css_value(tissue_request_formset):
    """
    This is used in the review overview process.

    First, it sort's the review table grid by the reviewing user's username.  It then converts the textual quantity review
    ("too much", "appropriate", "too little") to an integer matching the color scheme of the other two review columns (priority
    and scientific merit).

    Argument expected value:
        tissue_request_formset = TissueRequestFormSet(queryset=req_request.tissue_request_set.all(), prefix='tissue_requests')
    """
    # for every form in the formset
    for tissue_request_form in tissue_request_formset:
        # get the form's corresponding TissueRequest instance
        tissue_request = tissue_request_form.instance
        # and create a collection of TissueRequestReview instances, sorted by the reviewers' usernames
        tissue_request.sorted_tissue_request_reviews = sorted(tissue_request.get_reviews(), key=lambda x: x.review.user.username)
        # for every TissueRequestReview in this sorted collection
        for tissue_request_review in tissue_request.sorted_tissue_request_reviews:
            # if the VTR has been reviewed and submitted correctly
            if tissue_request_review.is_finished():
                # then give that review a property (later used by the template) representing the integer equivalent of the quantity review
                tissue_request_review.quantity_css_value = tissue_request_review.get_quantity(css=True)

def get_or_create_cart(request, cohort):
    """
    Again, a pretty self-explanatory name, but there's a hack so pay attention.

    If the user doesn't have a cart yet, it will create a new Request for cohort with RequestStatus.Cart.

    If the cart already exists, it'll check to make sure the current cart.cohort == cohort argument.
        If it's ==, it'll just return the cart_request it just found.
        if it's !=:
            If the cart is empty, it'll inexplicably delete the old cart and create a new one.
                Honestly, I don't know why it deletes it except _maybe_ to update req_request_date.
            If the cart is not empty, it will return None.
                This None is IMPORTANT and this is why you have to PAY ATTENTION.  the tissue_shop_detail_view view will test
                to see if this function returns a None.  This return value signals that the user has a cart, with tissues in it
                and is trying to request tissues from a DIFFERENT cohort.  This is no bueno, users can only request tissue from
                one cohort at a time.  When tissue_shop_detail_view gets a None, instead of a Request, it will redirect the user
                to another page asking them if they want to abort their new request because they already have a cart, or delete
                their current cart and create a new cart with the new cohort.
    """
    # get the user's cart if it already exists
    user_carts = Request.objects.cart().filter(user=request.user.id)
    if user_carts.count():
        cart_request = user_carts.get(user=request.user.id) # there should only ever be 1 request per user with RequestStatus.Cart
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
    """
    This is a handy little code snippet.  It ought to be used by any view which uses pagination.  It does some basic
    error handling and returns the requested page of the paginated collection.

    The function will return whatever paginator.page() returns.

    Arguments:
        request:  HTTPRequest instance, same thing passed into all views.  This is used to try and find a 'page' value in the
                  request's GET collection.  If it exists, it'll use it to return the requested page of the paginated collection.
                  Otherwise it'll do some error handling and return either the first or the last page.
        queryset:  This doesn't actually need to be a queryset, just a consistently-sorted iterable.  Either way, this is what
                   the paginator object will flip thru and return the proper page requested.
        count:  How many elements of queryset per page.
    """
    paginator = Paginator(queryset, count)
    # Make sure page request is an int. If not, deliver first page.
    try:
        page = int(request.GET.get('page', '1'))
    except ValueError:
        page = 1
    # If page request is out of range, deliver last page of results.
    try:
        paged = paginator.page(page)
    except (EmptyPage, InvalidPage):
        paged = paginator.page(paginator.num_pages)
    return paged

def export_template_to_pdf(template, context={}, outfile=None, return_pisaDocument=False):
    t = loader.get_template(template)
    c = Context(context)
    r = t.render(c)

    result = outfile if outfile else StringIO.StringIO()
    pdf = pisa.pisaDocument(StringIO.StringIO(r.encode("UTF-8")), dest=result)

    if not pdf.err:
        if return_pisaDocument:
            return pdf
        else:
            return result
    else:
        raise Exception(pdf.err)


