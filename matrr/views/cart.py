from datetime import datetime
from django.db import DatabaseError
from django.http import Http404
from django.shortcuts import render_to_response, redirect
from django.template import RequestContext
from django.contrib import messages
from matrr.forms import TissueRequestForm, CartCheckoutForm
from matrr.models import TissueRequest

def cart_view(request):
    # get the context (because it loads the cart as well)
    context = RequestContext(request)
    if context['cart_exists']:
        cart_request = context['cart']
        cohort = cart_request.cohort

        return render_to_response('matrr/cart/cart_page.html', {
        #'form': tissue_request_form,
        'cohort': cohort, },
                                  context_instance=RequestContext(request))
    else:
        return render_to_response('matrr/cart/cart_page.html', {},
                                  context_instance=RequestContext(request))


def cart_delete(request):
    # get the context (because it loads the cart as well)
    context = RequestContext(request)
    if request.method != 'POST':
        # provide the cart deletion form
        return render_to_response('matrr/cart/cart_delete.html', {},
                                  context_instance=RequestContext(request))
    elif request.POST['submit'] == 'yes':
        # delete the cart
        try:
            cart = context['cart']
        except DatabaseError:
            messages.error(request, 'Caught a database exception.')
        except KeyError:
            messages.error(request, 'There was no cart to delete.')
        else:
            cart.delete()
            messages.success(request, 'Cart deleted.')

    else:
        messages.info(request, 'Your cart was not deleted.')
    return redirect('/cart')


def cart_item_view(request, tissue_request_id):
    # get the context (because it loads the cart as well)
    context = RequestContext(request)
    # get the cart item
    cart_item = TissueRequest.objects.get(rtt_tissue_request_id=tissue_request_id)

    if cart_item not in context['cart_items']:
        raise Http404('This page does not exist.')
    if request.method != 'POST' or request.POST['submit'] == 'edit':
        # create a form so the item can be edited
        tissue_request_form = TissueRequestForm(instance=cart_item,
                                                req_request=cart_item.req_request,
                                                tissue=cart_item.get_tissue())
        return render_to_response('matrr/cart/cart_item.html', {'form': tissue_request_form,
                                                                'cohort': cart_item.req_request.cohort,
                                                                'tissue': cart_item.get_tissue(),
                                                                'cart_item': cart_item, },
                                  context_instance=context)
    else:
        if request.POST['submit'] == 'cancel':
            messages.info(request, 'No changes were made.')
            return redirect('/cart')
        elif request.POST['submit'] == 'delete':
            return delete_cart_item(request, cart_item)
        else:
            # validate the form and update the cart_item
            tissue_request_form = TissueRequestForm(instance=cart_item,
                                                    data=request.POST,
                                                    req_request=cart_item.req_request,
                                                    tissue=cart_item.get_tissue())
            if tissue_request_form.is_valid():
                # the form is valid, so update the tissue request
                tissue_request_form.save()
                messages.success(request, 'Item updated.')
                return redirect('/cart')
            else:
                return render_to_response('matrr/cart/cart_item.html', {'form': tissue_request_form,
                                                                        'cohort': cart_item.req_request.cohort,
                                                                        'tissue_type': cart_item.get_tissue(),
                                                                        'cart_item': cart_item, },
                                          context_instance=context)


def cart_item_delete(request, tissue_request_id):
    # get the context (because it loads the cart as well)
    context = RequestContext(request)
    # get the cart item
    cart_item = TissueRequest.objects.get(rtt_tissue_request_id=tissue_request_id)
    if cart_item not in context['cart_items']:
        raise Http404('This page does not exist.')
    return delete_cart_item(request, cart_item)


def delete_cart_item(request, cart_item):
    cart_item.delete()
    messages.success(request, 'Item removed from cart.')
    return redirect('/cart')


def cart_checkout(request):
    # get the context (because it loads the cart as well)
    context = RequestContext(request)
    if not context['cart_exists']:
        return render_to_response('matrr/cart/cart_checkout.html', {}, context_instance=context)
    cart_request = context['cart']
    if request.method != 'POST':
        checkout_form = CartCheckoutForm(instance=cart_request)
        return render_to_response('matrr/cart/cart_checkout.html', {'form': checkout_form}, context_instance=context)
    else:
        data = request.POST.copy()
        data['user'] = cart_request.user.id
        data['req_status'] = cart_request.req_status
        data['cohort'] = cart_request.cohort.coh_cohort_id
        checkout_form = CartCheckoutForm(request.POST, request.FILES, instance=cart_request)

        if checkout_form.is_valid() and request.POST['submit'] == 'checkout':
            cart_request.req_experimental_plan = checkout_form.cleaned_data['req_experimental_plan']
            cart_request.req_notes = checkout_form.cleaned_data['req_notes']
            cart_request.req_request_date = datetime.now()
            cart_request.submit_request()
            cart_request.save()

            messages.success(request, 'Tissue Request Submitted.')
            return redirect('/')
        else:
            return render_to_response('matrr/cart/cart_checkout.html', {'form': checkout_form},
                                      context_instance=context)
