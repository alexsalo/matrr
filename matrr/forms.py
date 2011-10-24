from django import forms
from django.forms import Form, ModelForm, CharField, widgets, ModelMultipleChoiceField, RegexField,Textarea
from django.forms.models import inlineformset_factory
from django.db import transaction
from django.contrib.admin.widgets import FilteredSelectMultiple
from datetime import date, timedelta
import re
from django.core.mail import send_mail
from django.core.urlresolvers import reverse

from matrr.models import *
from matrr.widgets import *
from registration.forms import RegistrationForm

FIX_CHOICES = (('', '---------'), ('Flash Frozen', 'Flash Frozen'),
			   ('4% Paraformaldehyde', '4% Paraformaldehyde'),
			   ('Fresh', 'Fresh'),
			   ('other', 'other'))


def trim_help_text(text):
	return re.sub(r' Hold down .*$', '', text)

#from django.forms.util import ErrorList
# 
class OtOAcountForm(ModelForm):
	username = CharField()
	first_name = CharField()
	last_name = CharField()
	email = EmailField()
	
#	This would be needed if we want to edit user through account + save data from fields
#	def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
#                 initial=None, error_class=ErrorList, label_suffix=':',
#                 empty_permitted=False, instance=None):
#		super(OtOAcountForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance)
#		if instance:
#			self.fields['username'].initial = self.instance.user.username
#			self.fields['first_name'].initial = self.instance.user.first_name
#			self.fields['last_name'].initial = self.instance.user.last_name
#			self.fields['email'].initial = self.instance.user.email
	class Meta:
		model = Account

class MatrrRegistrationForm(RegistrationForm):
	first_name = CharField(label="First name", max_length=30)
	last_name = CharField(label="Last name", max_length=30)
	institution = CharField(label="Institution", max_length=60)
	phone_number = RegexField(regex=r'^[0-9]{10}$',max_length=10,label="Phone number")
	address = CharField(label="Address", widget=Textarea(attrs={'cols': '40', 'rows': '5'}), max_length=350)

	def save(self, profile_callback=None):
		user = super(MatrrRegistrationForm, self).save(profile_callback)
		user.last_name = self.cleaned_data['last_name']
		user.first_name = self.cleaned_data['first_name']
		user.save()
		account = Account(user=user)
		account.institution = self.cleaned_data['institution']
		account.phone_number = self.cleaned_data['phone_number']
		account.address = self.cleaned_data['address']
		account.save()
		subject = "New account on www.matrr.com"
		body = "New account %s created. Go to %s to verify the account (check verified and save)." % (user.username,
							 "http://gleek.ecs.baylor.edu/admin/matrr/account/" + str(user.id))
		from_e = "Erich_Baker@baylor.edu"
		to_e = list()
		to_e.append(from_e)
		send_mail(subject, body, from_e, to_e, fail_silently=True)
		return user

class TissueRequestForm(ModelForm):
	def __init__(self, req_request, tissue, *args, **kwargs):
		self.instance = None
		self.req_request = req_request
		self.tissue = tissue
		super(TissueRequestForm, self).__init__(*args, **kwargs)
		self.fields['rtt_fix_type'].required = False
		self.fields['monkeys'].widget = CheckboxSelectMultipleLinkByTableNoVerification(link_base=self.req_request.cohort.coh_cohort_id, tissue=self.tissue,
																		)
		self.fields['monkeys'].queryset = self.req_request.cohort.monkey_set.all()
		# change the help text to match the checkboxes
		self.fields['monkeys'].help_text = trim_help_text(unicode(self.fields['monkeys'].help_text))

	def get_request_id(self):
		return self.instance.rtt_tissue_request_id

	def clean(self):
		super(TissueRequestForm, self).clean()
		cleaned_data = self.cleaned_data

		if not self.req_request.cohort.coh_upcoming or cleaned_data['rtt_fix_type'] == "":
			cleaned_data['rtt_fix_type'] = "Flash Frozen"
		fix_type = cleaned_data.get('rtt_fix_type')

		if self.req_request and self.tissue and fix_type \
		and (self.instance is None		or		(self.instance.rtt_tissue_request_id is not None and self.instance.rtt_fix_type != fix_type )) \
		and TissueRequest.objects.filter(req_request=self.req_request,tissue_type=self.tissue,rtt_fix_type=fix_type).count() > 0:
			raise forms.ValidationError("You already have this tissue and fix in your cart.")

		# Always return the full collection of cleaned data.
		return cleaned_data

	class Meta:
		model = TissueRequest
		exclude = ('req_request', 'tissue_type', 'accepted_monkeys')
		widgets = {'rtt_fix_type': FixTypeSelection(choices=FIX_CHOICES)}


class CartCheckoutForm(ModelForm):
	def clean(self):
		super(CartCheckoutForm, self).clean()
		if not self.cleaned_data.get('req_progress_agreement'):
			raise forms.ValidationError('You must agree to submit a progress report.')
		if not self.cleaned_data.get('req_safety_agreement'):
			raise forms.ValidationError("You must acknowledge you understand the risks of shipping potential biohazards.")
		return self.cleaned_data


	class Meta:
		model = Request
		exclude = ('request_status', 'req_report_asked')
		widgets = {'req_project_title': forms.TextInput(attrs={'size': 50})}


class ReviewForm(ModelForm):
	def __init__(self, *args, **kwargs):
		TissueRequestReviewFormSet = inlineformset_factory(Review,
														   TissueRequestReview,
														   extra=0,
														   can_delete=False, )

		self.tissue_request_formset = TissueRequestReviewFormSet(prefix='peripherals', *args, **kwargs)

		super(ReviewForm, self).__init__(*args, **kwargs)

	def is_valid(self):
		return self.tissue_request_formset.is_valid()\
		and super(ReviewForm, self).is_valid()

	@transaction.commit_on_success
	def save(self, commit=True):
		super(ReviewForm, self).save(commit)
		self.tissue_request_formset.save(commit)

	class Meta:
		model = Review


class AccountForm(ModelForm):
	class Meta:
		model = Account


class MtaForm(ModelForm):
	class Meta:
		model = Mta


class CodForm(ModelForm):
	def __init__(self, *args, **kwargs):
		cohort = ''
		if 'cohort' in kwargs:
			cohort = kwargs.pop('cohort')
		super(CodForm, self).__init__(*args, **kwargs)
		self.fields['cohort'].queryset = Cohort.objects.all()
		self.fields['cohort'].initial = cohort

	class Meta:
		model = CohortData


class RudForm(ModelForm):
	def __init__(self, user, *args, **kwargs):
		super(RudForm, self).__init__(*args, **kwargs)
		upload_from = date.today() - timedelta(days=30)
		self.fields['request'].queryset = Request.objects.filter(user=user, request_status__rqs_status_name='Shipped', shipment__shp_shipment_date__lte=upload_from)
	
	class Meta:
		model = ResearchUpdate


class ReviewResponseForm(Form):
	subject = CharField(max_length=200, widget=widgets.TextInput(attrs={'size': 130}))
	body = CharField(widget=widgets.Textarea(attrs={'cols': 94,
													'rows': 20}))

	def __init__(self, tissue_requests, *args, **kwargs):
		self.tissue_requests = tissue_requests
		super(ReviewResponseForm, self).__init__(*args, **kwargs)
		for tissue_request in self.tissue_requests:
			if tissue_request.get_tissue():
				self.fields[str(tissue_request)] = ModelMultipleChoiceField(queryset=tissue_request.monkeys.all(),
																			required=False,
																			widget=GroupedCheckboxSelectMultipleMonkeys(
																				tissue_request=tissue_request)
				)


class FulltextSearchForm(Form):
	terms = CharField(label='Search', widget=widgets.TextInput(attrs={'size': 40}))


class ContactUsForm(Form):
	email_subject = CharField(max_length=200, widget=widgets.TextInput(attrs={'size': 40}))
	email_from = EmailField(widget=widgets.TextInput(attrs={'size': 40}))
	email_body = CharField(widget=widgets.Textarea(attrs={'cols': 40, 'rows': 15}))


class TissueRequestProcessForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(ModelForm, self).__init__(*args, **kwargs)
		self.fields['accepted_monkeys'].widget = CheckboxSelectMultipleLinkByTable(link_base=self.instance.req_request.cohort.coh_cohort_id,
																			tissue=self.instance.get_tissue(),
																			tis_request=self.instance)
		self.fields['accepted_monkeys'].required = False
		self.fields['accepted_monkeys'].queryset = self.instance.monkeys.all()
		# change the help text to match the checkboxes
		self.fields['accepted_monkeys'].help_text = ''


	class Meta:
		model = TissueRequest
		fields = ('accepted_monkeys',)


class TissueInventoryVerificationForm(Form):
	primarykey = IntegerField(widget=HiddenInput(), required=False)
	freezer = CharField(max_length=100, required=False)
	location = CharField(max_length=100, required=False)
	quantity = DecimalField(required=False)
	units = ModelChoiceField(queryset=Unit.objects.all(), required=False)
	details = CharField(widget=widgets.Textarea(attrs={'cols': 40, 'rows': 2, 'style':"width:100%;",}), required=False)
	inventory = ChoiceField(choices=InventoryStatus, required=False)
