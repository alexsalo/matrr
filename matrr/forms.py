#encoding=utf-8
from django import forms
from django.forms import Form, ModelForm, CharField, widgets, ModelMultipleChoiceField, RegexField,Textarea
from django.forms.extras.widgets import SelectDateWidget
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
			   ('DNA', 'DNA'),
			   ('RNA', 'RNA'),
			   ('other', 'other'))


def trim_help_text(text):
	return re.sub(r' Hold down .*$', '', text)

#from django.forms.util import ErrorList
# 
class OtOAcountForm(ModelForm):
	username = CharField(required = False)
	first_name = CharField(required = False)
	last_name = CharField(required = False)
	email = EmailField(required = False)
	
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

def generate_email_body_new_registration(account):
	
	body = "New account was created.\n" + \
				"\t username: %s\n" % account.user.username + \
				"\t first name: %s\n" % account.user.first_name + \
				"\t last name: %s\n" % account.user.last_name + \
				"\t e-mail: %s\n" % account.user.email + \
				"\t phone number: %s\n" % account.phone_number + \
				"\t institution: %s\n" % account.institution + \
				"\t first name: %s\n" % account.user.first_name + \
				"\t address 1: %s\n" % account.act_real_address1 + \
				"\t address 2: %s\n" % account.act_real_address2 + \
				"\t city: %s\n" % account.act_real_city + \
				"\t ZIP code: %s\n" % account.act_real_zip + \
				"\t state: %s\n" % account.act_real_state + \
			"\nTo view account in admin, go to:\n" + \
				"\t http://gleek.ecs.baylor.edu/admin/matrr/account/%d/\n" % account.user.id + \
			"To verify account follow this link:\n" + \
				"\t http://gleek.ecs.baylor.edu%s\n" % reverse('account-verify', args=[account.user.id,]) + \
			"To delete account follow this link and confirm deletion of all objects (Yes, I'm sure):\n" + \
				"\t http://gleek.ecs.baylor.edu/admin/auth/user/%d/delete/\n" % account.user.id + \
			"All the links might require a proper log-in."
	return body

class MatrrRegistrationForm(RegistrationForm):
	first_name = CharField(label="First name", max_length=30)
	last_name = CharField(label="Last name", max_length=30)
	institution = CharField(label="Institution", max_length=60)
	phone_number = RegexField(regex=r'^[0-9]{10}$',max_length=10,label="Phone number")
#	address = CharField(label="Address", widget=Textarea(attrs={'cols': '40', 'rows': '5'}), max_length=350)
	act_real_address1 =CharField(label='Address 1',max_length=50,)
	act_real_address2 =CharField(label='Address 2',max_length=50,required=False)
	act_real_city = CharField(label='City',max_length=25, )
	act_real_state =CharField(label='State', max_length=2,)
	act_real_zip =CharField(label='ZIP', max_length=10,)
	act_real_country =CharField(label='Country', max_length=25,required=False)


	def save(self, profile_callback=None):
		user = super(MatrrRegistrationForm, self).save(profile_callback)
		user.last_name = self.cleaned_data['last_name']
		user.first_name = self.cleaned_data['first_name']
		user.save()
		account = Account(user=user)
		account.institution = self.cleaned_data['institution']
		account.phone_number = self.cleaned_data['phone_number']
#		account.address = self.cleaned_data['address']
		account.act_real_address1 = self.cleaned_data['act_real_address1']
		account.act_real_address2 = self.cleaned_data['act_real_address2']
		account.act_real_city = self.cleaned_data['act_real_city']
		account.act_real_state = self.cleaned_data['act_real_state']
		account.act_real_zip = self.cleaned_data['act_real_zip']
		account.act_real_country = self.cleaned_data['act_real_country']
		
		account.act_address1 = account.act_real_address1
		account.act_address2 = account.act_real_address2
		account.act_city = account.act_real_city
		account.act_country = account.act_real_country
		account.act_state = account.act_real_state
		account.act_zip = account.act_real_zip
		account.act_shipping_name = user.first_name + " " + user.last_name
		
		account.save()
		subject = "New account on www.matrr.com"
		body = generate_email_body_new_registration(account)
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

		if fix_type == 'DNA' or fix_type == 'RNA':
			if cleaned_data['rtt_units'] != 'μg':
				raise forms.ValidationError("Requests for DNA or RNA units must be in micrograms.")

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


class ShippingAccountForm(ModelForm):
	class Meta:
		model = Account
		fields = ['act_shipping_name', 'act_fedex','act_country', 'act_zip', 'act_state', 'act_city', 'act_address2', 'act_address1'] 

class AddressAccountForm(ModelForm):
	class Meta:
		model = Account
		fields = [ 'act_real_address1', 'act_real_address2', 'act_real_city',  'act_real_zip', 'act_real_country', 'act_real_state']

class AccountForm(ModelForm):
	from django.forms.util import ErrorList
	first_name = CharField(label="First name", max_length=30)
	last_name = CharField(label="Last name", max_length=30)
	email = EmailField(label='Email')
	
	def save(self, commit=True):
		account = super(AccountForm, self).save(commit)
		account.user.first_name = self.cleaned_data['first_name']
		account.user.last_name = self.cleaned_data['last_name']
		account.user.email = self.cleaned_data['email']
		account.user.save()
	
	def __init__(self, data=None, files=None, auto_id='id_%s', prefix=None,
                 initial=None, error_class=ErrorList, label_suffix=':',
                 empty_permitted=False, instance=None):

		super(AccountForm, self).__init__(data, files, auto_id, prefix, initial, error_class, label_suffix, empty_permitted, instance)
		if instance:
			self.fields['first_name'].initial = self.instance.user.first_name
			self.fields['last_name'].initial = self.instance.user.last_name
			self.fields['email'].initial = self.instance.user.email
	class Meta:
		model = Account
		fields = ['institution', 'phone_number']
		
	

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
	units = ChoiceField(choices=Units, required=False)
	details = CharField(widget=widgets.Textarea(attrs={'cols': 40, 'rows': 2, 'style':"width:100%;",}), required=False)
	inventory = ChoiceField(choices=InventoryStatus, required=False)


class VIPGraphForm_dates(Form):
	from_date = DateField(widget=DateTimeWidget, required=False)
	to_date = DateField(widget=DateTimeWidget, required=False)

	def __init__(self, min_date=None, max_date=None, *args, **kwargs):
		super(VIPGraphForm_dates, self).__init__(*args, **kwargs)
		self.fields['from_date'].widget.attrs['min_date'] = min_date
		self.fields['from_date'].widget.attrs['max_date'] = max_date
		self.fields['to_date'].widget.attrs['min_date'] = min_date
		self.fields['to_date'].widget.attrs['max_date'] = max_date


class VIPGraphForm_cohorts(Form):
	cohort = ModelChoiceField(queryset=Cohort.objects.filter(cohort_drinking_experiment_set__gt=0).distinct().order_by('coh_cohort_name'))

class VIPGraphForm_monkeys(Form):
	monkey = ModelChoiceField(queryset=Monkey.objects.filter(mtd_set__gt=0).distinct().order_by('mky_id'))


class SpiffyForm(Form):
	OPERATORS = (
		("", "are equal to"),
		("__gte", "are greater than or equal to"),
		("__lte", "are less than or equal to"),
		("__gt", "are greater than"),
		("__lt", "are less than"),
		("__icontains", "contain (case insensitive"),
	)
	is_related = {}

	def __init__(self, list_of_fields, *args, **kwargs):
		from django.db.models.fields.related import ForeignKey, ManyToManyRel # i'm not sure about many2manyrel.  might be many2manyfield
		related = (ForeignKey, ManyToManyRel)
		super(SpiffyForm, self).__init__(*args, **kwargs)
		for index, key in enumerate(list_of_fields):
			name = key.name
			if isinstance(key, related):
				model = key.related.parent_model
				self.fields[name] = ModelMultipleChoiceField(queryset=model.objects.all(), required=False)
				self.fields[name].label = "Name"
				self.is_related[name] = True
			else:
				self.fields[name + "_operator"] = ChoiceField(choices=self.OPERATORS, required=False)
				self.fields[name + "_operator"].label = "Select " + name + "'s which "
				self.fields[name] = CharField(max_length=50, required=False)
				self.fields[name].label = ""
				self.is_related[name] = False

	def crazy_town_q_builder(self):
		from django.db.models import Q
		#this shit is nuts
		if self.is_valid(): # hooray, we have a valid form!
			data = self.cleaned_data # grab the spiffy data
			q_object = Q() # create an empty Q object, which we will populate with the spiffy data
			for field in self.fields: # fields is a list of the column _!objects!_ in the model
				if '_operator' in field:
					continue # we don't actually care about operator fields by themselves
				name = field # but the form uses the field names in cleaned_data
				if data[name]: # ignore empty data.  django doesn't let you query/filter empty strings.  IE: filter(column_name='') will error out.
					if not self.is_related[field]: # if this field is NOT a relation field (foreign key or m2m)
						q_dict = {name + data[name+"_operator"]: data[name]} # then we have to build the funky dictionary entry to join 'column_name' and '__gte'
						q_object = q_object & Q(**q_dict) # and finally AND this fresh-build query with any previous queries built
					else: # but wait, there's more!
						if len(data[name]): # if this field is a related field, and at least one was selected
							related_q = Q() # create an _different_ Q object, because related objects are first OR'd together, then AND'd with the other fields
							for datum in data[name]: # so for every related object selected
								q_dict = {name: datum} # create the funky Q object dictionary (which we immediatly unpack -.-)
								related_q = related_q | Q(**q_dict) # or the related Q objects together
							q_object = q_object & related_q # and then finally AND the related field Q objects with the other fields
			# return that sexy Q object
			return q_object # but only if .is_valid()
