from datetime import date, timedelta
from django.core.urlresolvers import reverse
from django.contrib.admin.views.decorators import staff_member_required
from django.shortcuts import render_to_response, redirect, get_object_or_404
from django.template import RequestContext
from django.contrib.auth.decorators import user_passes_test
from django.contrib import messages
from matrr import emails
from matrr.forms import AccountForm, AccountMTAForm, AddressAccountForm, ShippingAccountForm
#from matrr.models import *
from matrr.models import Account, Institution, Mta, DataFile, Shipment, ResearchUpdate, Request

@staff_member_required
def account_verify(request, user_id):
    account = get_object_or_404(Account, pk=user_id)
    if not account.verified:
        account.verified = True
        account.save()
        #		send email
        emails.send_account_verified_email(account)
        messages.success(request, "Account %s was successfully verified." % account.user.username)
    else:
        messages.info(request, "Account %s is already verified." % account.user.username)
    return render_to_response('base.html', {}, context_instance=RequestContext(request))


def account_info(request):
    # make address form if one does not exist
    if request.method == 'POST':
        form = AccountForm(data=request.POST, instance=request.user.account)
        if form.is_valid():
            # all the fields in the form are valid, so save the data
            form.save()
            messages.success(request, 'Account Info Saved')
            return redirect(reverse('account-view'))
    else:
        #create the form for shipping address
        form = AccountForm(instance=request.user.account)
    return render_to_response('matrr/account/account_info_form.html',
                              {'form': form,
                               'user': request.user
                              },
                              context_instance=RequestContext(request))


def account_mta(request):
    account = request.user.account
    if request.method == 'POST':
        form = AccountMTAForm(data=request.POST)
        if form.is_valid():
            institution = form.cleaned_data['institution'].ins_institution_name
            account.act_mta = institution
            account.save()

            if institution == "Non-UBMTA Institution":
                return redirect('mta-upload')
            #				messages.info(request, "If your institution is not part of the <acronym>, you must download, sign, scan, and upload a Material Transfer Agreement.  ")
            else:
                messages.success(request, 'Account Info Saved')
                return redirect(reverse('account-view'))
    else:
        try:
            institution = Institution.objects.get(ins_institution_name=account.act_mta)
        except Institution.DoesNotExist:
            institution = Institution.objects.get(ins_institution_name='Non-UBMTA Institution')
        form = AccountMTAForm(initial={'institution': institution})
    return render_to_response('matrr/account/account_mta.html',
                              {'form': form,
                               'user': request.user
                              },
                              context_instance=RequestContext(request))


def account_address(request):
    # make address form if one does not exist
    if request.method == 'POST':
        form = AddressAccountForm(data=request.POST, instance=request.user.account)
        if form.is_valid():
            # all the fields in the form are valid, so save the data
            form.save()
            messages.success(request, 'Account Address Saved')
            return redirect(reverse('account-view'))
    else:
        #create the form for shipping address
        form = AddressAccountForm(instance=request.user.account)
    return render_to_response('matrr/account/account_address_form.html',
                              {'form': form,
                               'user': request.user
                              },
                              context_instance=RequestContext(request))


def account_shipping(request):
    # make address form if one does not exist
    if request.method == 'POST':
        form = ShippingAccountForm(data=request.POST, instance=request.user.account)
        if form.is_valid():
            # all the fields in the form are valid, so save the data
            form.save()
            messages.success(request, 'Shipping Address Saved')
            return redirect(reverse('account-view'))
    else:
        #create the form for shipping address
        form = ShippingAccountForm(instance=request.user.account)
    return render_to_response('matrr/account/account_shipping_form.html',
                              {'form': form,
                               'user': request.user
                              },
                              context_instance=RequestContext(request))


def account_view(request):
    return account_detail_view(request=request, user_id=request.user.id)


def account_detail_view(request, user_id):
    if request.user.id == user_id:
        edit = True
    else:
        edit = False
    # get information from the act_account relation

    account_info = get_object_or_404(Account, pk=user_id)
    mta_info = Mta.objects.filter(user__id=user_id)
    data_files = DataFile.objects.filter(account__user=user_id)
    display_rud_from = date.today() - timedelta(days=30)
    urge_rud_from = date.today() - timedelta(days=90)
    pending_rud = Shipment.objects.filter(req_request__user=user_id, shp_shipment_date__lte=display_rud_from,
                                          shp_shipment_date__gte=urge_rud_from, req_request__rud_set=None)
    urged_rud = Shipment.objects.filter(req_request__user=user_id, shp_shipment_date__lte=urge_rud_from,
                                        req_request__rud_set=None)

    rud_info = ResearchUpdate.objects.filter(req_request__user=user_id)

    if pending_rud or urged_rud or rud_info:
        rud_on = True
    else:
        rud_on = False

    order_list = Request.objects.processed().filter(user__id=user_id).order_by("-req_request_date")[:20]

    return render_to_response('matrr/account/account.html',
                              {'account_info': account_info,
                               'mta_info': mta_info,
                               'data_files': data_files,
                               'rud_info': rud_info,
                               'rud_on': rud_on,
                               'pending_rud': pending_rud,
                               'urged_rud': urged_rud,
                               'order_list': order_list,
                               'edit': edit,
                              },
                              context_instance=RequestContext(request))


@user_passes_test(lambda u: u.has_perm('matrr.view_other_accounts'), login_url='/denied/')
def account_reviewer_view(request, user_id):
    return account_detail_view(request, user_id)


