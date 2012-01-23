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
		self.fields['monkeys'].widget = CheckboxSelectMultipleLinkByTableNoVerification(link_base=self.req_request.cohort.coh_cohort_id,
																					tissue=self.tissue)
		# the first time the form is created the instance does not exist
		if self.instance.pk:
			accepted = self.instance.accepted_monkeys.all().values_list('mky_id', flat=True)
		else:
			accepted = list()
		print accepted
		self.fields['monkeys'].queryset = self.req_request.cohort.monkey_set.all().exclude(mky_id__in=accepted)
		
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

		# If a user requests DNA/RNA of bone marrow tissue (maybe never), the units will be forced in micrograms, not microliters.  I think this is correct.
		if fix_type == 'DNA' or fix_type == 'RNA':
			if cleaned_data['rtt_units'] != 'ug':
				raise forms.ValidationError("Units of DNA or RNA must be in micrograms.")
		elif "marrow" in self.tissue.tst_tissue_name.lower():
			if cleaned_data['rtt_units'] != 'ul':
				raise forms.ValidationError("Units of bone marrow must be in microliters.")

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
		exclude = ('req_status', 'req_report_asked')
		widgets = {'req_project_title': forms.TextInput(attrs={'size': 50})}


class PurchaseOrderForm(ModelForm):
	class Meta:
		model = Request
		fields = ('req_purchase_order',)


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
		self.fields['request'].queryset = Request.objects.filter(user=user, req_status=RequestStatus.Shipped, shipment__shp_shipment_date__lte=upload_from)
	
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


class RawDataUploadForm(Form):
	data = FileField()

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
	quantity = FloatField(required=False)
	units = ChoiceField(choices=Units, required=False)
	details = CharField(widget=widgets.Textarea(attrs={'cols': 40, 'rows': 2, 'style':"width:100%;",}), required=False)
	inventory = ChoiceField(choices=InventoryStatus, required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer))


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


class FilterForm_basic(Form):
	# Mostly deprecated (before it was even used)
	# this form provides 1 set of filter options for each field passed into it.
	# FilterForm is more flexible, supports more fields, and is better commented.  Probably.
	NUMERIC_OPERATORS = (
		("", "equal to"),
		("__gte", "greater than or equal to"),
		("__lte", "less than or equal to"),
		("__gt", "greater than"),
		("__lt", "less than"),
	)
	CHAR_OPERATORS = (
		("__iexact", "is"),
		("__icontains", "contains"),
	)
	has_operator = {}

	def __init__(self, list_of_fields, *args, **kwargs):
		from django.db.models import fields
		integers = (fields.IntegerField, fields.AutoField)
		related = (fields.related.ForeignKey, fields.related.ManyToManyRel)
		super(FilterForm_basic, self).__init__(*args, **kwargs)
		for key in list_of_fields:
			name = key.name
			if isinstance(key, related):
				model = key.related.parent_model
				self.fields[name] = ModelMultipleChoiceField(queryset=model.objects.all(), required=False)
				self.fields[name].label = "Relation: " + name
				self.has_operator[name] = False
			elif isinstance(key, integers):
				self.fields[name + "_operator"] = ChoiceField(choices=self.NUMERIC_OPERATORS, required=False)
				self.fields[name + "_operator"].label = key.verbose_name
				self.fields[name] = IntegerField(required=False)
				self.fields[name].label = ""
				self.has_operator[name] = True
			elif isinstance(key, fields.FloatField):
				self.fields[name + "_operator"] = ChoiceField(choices=self.NUMERIC_OPERATORS, required=False)
				self.fields[name + "_operator"].label = key.verbose_name
				self.fields[name] = FloatField(required=False)
				self.fields[name].label = ""
				self.has_operator[name] = True
			elif isinstance(key, fields.BooleanField):
				self.fields[name] = NullBooleanField(required=False)
				self.fields[name].label = key.verbose_name
				self.has_operator[name] = False
			else:
				self.fields[name + "_operator"] = ChoiceField(choices=self.CHAR_OPERATORS, required=False)
				self.fields[name + "_operator"].label = key.verbose_name
				self.fields[name] = CharField(max_length=50, required=False)
				self.fields[name].label = ""
				self.has_operator[name] = True

	def get_q_object(self):
		from django.db.models import Q
		#this shit is crazy
		if self.is_valid(): # hooray, we have a valid form!
			data = self.cleaned_data # grab the spiffy data
			q_object = Q() # create an empty Q object, which we will populate with the spiffy data
			for field in self.fields: # fields is a list of the column _!objects!_ in the model
				if '_operator' in field:
					continue # we don't actually care about operator fields by themselves
				name = field # but the form uses the field names in cleaned_data
				if data[name] is None or str(data[name]) is "": # the str() is a hack because u"" != "".  Feels safer to convert to the test that to assume it's unicode
					continue
				else: # ignore empty data.  django doesn't let you query/filter empty strings.  IE: filter(column_name='') will error out.
					if self.has_operator[field]: # if this field has an operator field
						q_dict = {name + data[name+"_operator"]: data[name]} # then we have to build the funky dictionary entry to join 'column_name' and '__gte'
						q_object = q_object & Q(**q_dict) # and finally AND this fresh-build query with any previous queries built
					else: # but wait, there's more!
						if data[name] is True or data[name] is False:
							q_dict = {name: data[name]}
							q_object = q_object & Q(**q_dict)
						else:
							related_q = Q() # create an _different_ Q object, because related objects are first OR'd together, then AND'd with the other fields
							for datum in data[name]: # so for every related object selected
								q_dict = {name: datum} # create the funky Q object dictionary (which we immediately unpack -.-)
								related_q = related_q | Q(**q_dict) # or the related Q objects together
							q_object = q_object & related_q # and then finally AND the related field Q objects with the other fields
			# return that sexy Q object
			return q_object # but only if .is_valid()


class FilterForm(Form):
	"""
	This form creates 3 fields for every model field passed into it.  This allows the user to choose which field to filter, which operator to filter
	with, and value to filter.  FilterForm.build_Q() will create and return a Q object from the filled out form fields.  In the view you pass
	this into the chosen model's filter method.

	eg:
	filter_form=FilterForm(Monkey._meta.fields)
	<user input>
	Monkey.objects.filter(filter_form.build_Q())
	"""
	NUMERIC_OPERATORS = (
		("", "equal to"),
		("__gte", "greater than or equal to"),
		("__lte", "less than or equal to"),
		("__gt", "greater than"),
		("__lt", "less than"),
	)
	CHAR_OPERATORS = (
		("__iexact", "is"),
		("__icontains", "contains"),
	)

	# I was getting an issue with init being called several times after the filter was initialized (page reloads, i'm pretty sure)
	# This caused these choice fields to collect duplicate choices, so I made them sets.
	INT_FIELD_CHOICES = set()
	FLOAT_FIELD_CHOICES = set()
	CHAR_FIELD_CHOICES = set()
	BOOL_FIELD_CHOICES = set()
	DISCRETE_FIELD_CHOICES = set()

	count = 0

	# does not handle date/datetime fields (yet)
	def __init__(self, list_of_model_fields, number_of_fields=4, *args, **kwargs):
		from django.db.models import fields
		super(FilterForm, self).__init__(*args, **kwargs)

		# Create the field categories
		integers = (fields.IntegerField, fields.AutoField, fields.BigIntegerField, fields.PositiveIntegerField, fields.PositiveSmallIntegerField, fields.SmallIntegerField)
		related = (fields.related.ForeignKey, fields.related.ManyToManyRel)
		dates = (fields.DateTimeField, fields.DateField)
		chars = (fields.CharField, fields.TextField)
		bools = (fields.BooleanField, fields.NullBooleanField)

		int_fields = []
		related_fields = []
		float_fields = []
		date_fields = []
		discrete_fields = []
		bool_fields = []
		char_fields = []
		# Separate each of list_of_model_fields' objects into categories
		# and create the Choices objects for each category
		for field in list_of_model_fields:
			if field.choices:
				discrete_fields.append(field)
				self.DISCRETE_FIELD_CHOICES.add((field.name, field.verbose_name))
			elif isinstance(field, integers):
				int_fields.append(field)
				self.INT_FIELD_CHOICES.add((field.name, field.verbose_name))
			elif isinstance(field, fields.FloatField):
				float_fields.append(fields.FloatField)
				self.FLOAT_FIELD_CHOICES.add((field.name, field.verbose_name))
			elif isinstance(field, dates):
				date_fields.append(field)
				# Do something fancy?
				continue
			elif isinstance(field, related):
				related_fields.append(field)
			elif isinstance(field, chars):
				self.CHAR_FIELD_CHOICES.add((field.name, field.verbose_name))
				char_fields.append(field)
			elif isinstance(field, bools):
				self.BOOL_FIELD_CHOICES.add((field.name, field.verbose_name))
				bool_fields.append(field)
			else:
				print "panic"
				print field.name
				continue

		# These loops create the form field 'sets', denoted by the field name.
		# field names fit the format "<index> <category> <purpose>"
		# <index>: The index groups the form fields into field sets
		# <category>: The category name is used in build_Q() to apply appropriate functionality to a given field set
		# <purpose>: Indicates what the value stored in the field does
		number_of_fields = int(number_of_fields) # mostly to catch sloppy programmers
		for i, field in enumerate(int_fields, 1):
			if i > number_of_fields: break
			i = str(i)
			self.fields[i + ' Num-Int Choice'] = ChoiceField(choices=self.INT_FIELD_CHOICES, required=False)
			self.fields[i + ' Num-Int Choice'].label = "Integer %s" % i
			self.fields[i + ' Num-Int Choice'].help_text = "Choose an integer property to filter."
			self.fields[i + ' Num-Int Operator'] = ChoiceField(choices=self.NUMERIC_OPERATORS, required=False)
			self.fields[i + ' Num-Int Operator'].label = 'Integer %s Operator' % i
			self.fields[i + ' Num-Int Operator'].help_text = "Choose an operator to apply to the chosen field."
			self.fields[i + ' Num-Int Value'] = CharField(max_length=50, required=False)
			self.fields[i + ' Num-Int Value'].label = "Integer %s Value" % i
			self.fields[i + ' Num-Int Value'].help_text = "Enter a whole-number value to filter the chosen field."
			self.fields[i + ' Num-Int Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer,
																										   choices=(('AND','AND'),('OR','OR')) ),initial="AND" )
			self.fields[i + ' Num-Int Logical'].label = "Integer %s Combine" % i
			self.fields[i + ' Num-Int Logical'].help_text = "AND this field with the other or OR them together."
		for i, field in enumerate(float_fields, 1):
			if i > number_of_fields: break
			i = str(i)
			self.fields[i + ' Num-Float Choice'] = ChoiceField(choices=self.FLOAT_FIELD_CHOICES, required=False)
			self.fields[i + ' Num-Float Choice'].label = 'Float %s.0' % i
			self.fields[i + ' Num-Float Choice'].help_text = "Choose a float property to filter."
			self.fields[i + ' Num-Float Operator'] = ChoiceField(choices=self.NUMERIC_OPERATORS, required=False)
			self.fields[i + ' Num-Float Operator'].label = 'Float %s.0 Operator' % i
			self.fields[i + ' Num-Float Operator'].help_text = "Choose an operator to apply to the chosen field."
			self.fields[i + ' Num-Float Value'] = CharField(max_length=50, required=False)
			self.fields[i + ' Num-Float Value'].label = "Float %s.0 Value" % i
			self.fields[i + ' Num-Float Value'].help_text = "Enter a float value to filter the chosen field."
			self.fields[i + ' Num-Float Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer,
																											 choices=(('AND','AND'),('OR','OR')) ),initial="AND" )
			self.fields[i + ' Num-Float Logical'].label = "Float %s Combine" % i
			self.fields[i + ' Num-Float Logical'].help_text = "AND this field with the other or OR them together."
		for i, field in enumerate(char_fields, 1):
			if i > number_of_fields: break
			i = str(i)
			self.fields[i + ' Char Choice'] = ChoiceField(choices=self.CHAR_FIELD_CHOICES, required=False)
			self.fields[i + ' Char Choice'].label = "Char %s" % i
			self.fields[i + ' Char Choice'].help_text = "Choose a text property to filter."
			self.fields[i + ' Char Operator'] = ChoiceField(choices=self.CHAR_OPERATORS, required=False)
			self.fields[i + ' Char Operator'].label = "Char %s Operator" % i
			self.fields[i + ' Char Operator'].help_text = "Choose an operator to apply to the chosen field."
			self.fields[i + ' Char Value'] = CharField(max_length=50, required=False)
			self.fields[i + ' Char Value'].label = "Char %s Value" % i
			self.fields[i + ' Char Value'].help_text = "Enter text by which to filter the chosen field."
			self.fields[i + ' Char Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer,
																										choices=(('AND','AND'),('OR','OR')) ),initial="AND" )
			self.fields[i + ' Char Logical'].label = "Char %s Combine" % i
			self.fields[i + ' Char Logical'].help_text = "AND this field with the other or OR them together."
		for i, field in enumerate(bool_fields, 1):
			if i > number_of_fields: break
			i = str(i)
			self.fields[i + ' Bool Choice'] = ChoiceField(choices=self.BOOL_FIELD_CHOICES, required=False)
			self.fields[i + ' Bool Choice'].label = "Bool %s" % i
			self.fields[i + ' Bool Choice'].help_text = "Choose a Boolean field to filter."
			self.fields[i + ' Bool Value'] = NullBooleanField(required=False) # NullBoolean is important, otherwise the user _must_ filter the bool field
			self.fields[i + ' Bool Value'].label = "Bool %s Value" % i
			self.fields[i + ' Bool Value'].help_text = "Choose how to filter the Boolean field"
			self.fields[i + ' Bool Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer,
																										choices=(('AND','AND'),('OR','OR')) ),initial="AND" )
			self.fields[i + ' Bool Logical'].label = "Bool %s Combine" % i
			self.fields[i + ' Bool Logical'].help_text = "AND this field with the other or OR them together."
		for i, field in enumerate(discrete_fields, 1):
			i = str(i)
			name = field.name
			choices = list(field.choices)
			choices.append(("", 'None')) # The empty choice let the choice fields be excluded from the filter on submit
			self.fields[i + ' Discrete Choice'] = ChoiceField(choices=self.DISCRETE_FIELD_CHOICES, required=False)
			self.fields[i + ' Discrete Choice'].label = "Discrete %s" % i
			self.fields[i + ' Discrete Choice'].help_text = "Choose a Discrete field to filter."
			self.fields[i + ' Discrete Value'] = ChoiceField(choices=choices, required=False)
			self.fields[i + ' Discrete Value'].label = "Discrete %s Value" % i
			self.fields[i + ' Discrete Value'].help_text = "Choose how to filter the Discrete field"
			self.fields[i + ' Discrete Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer,
																											choices=(('AND','AND'),('OR','OR')) ),initial="AND" )
			self.fields[i + ' Discrete Logical'].label = "Discrete %s Combine" % i
			self.fields[i + ' Discrete Logical'].help_text = "AND this field with the other or OR them together."
		for i, field in enumerate(related_fields, 1):
			i = str(i)
			name = field.name
			model = field.related.parent_model
			self.fields[i + ' Related Value'] = ModelMultipleChoiceField(queryset=model.objects.all(), required=False)
			self.fields[i + ' Related Value'].label = "Relation: %s" % name
			self.fields[i + ' Related Value'].help_text = field.help_text
			self.fields[i + ' Related Value'].field_name = name
			self.fields[i + ' Related extra-Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer,
																												 choices=(('AND','AND'),('OR','OR')) ),initial="AND" )
			self.fields[i + ' Related extra-Logical'].label = "Relation %s extra-Combine" % i
			self.fields[i + ' Related extra-Logical'].help_text = "AND this field with the other fields or OR them together."
			self.fields[i + ' Related intra-Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=HorizRadioRenderer,
																												 choices=(('AND','AND'),('OR','OR')) ),initial="OR" )
			self.fields[i + ' Related intra-Logical'].label = "Relation %s intra-Combine" % i
			self.fields[i + ' Related intra-Logical'].help_text = "AND each related object together or OR them together."


	def get_q_object(self):
		from django.db.models import Q
		# Welcome to the Crazy-town Q factory
		if self.is_valid(): # hooray, we have a valid form!
			data = self.cleaned_data # grab the spiffy data
			q_object = Q() # create an empty Q object, which we will populate with the spiffy data
			for name, value in data.items(): # fields is a list of the column _!objects!_ in the model
				_index, _category, _purpose = name.split(' ')
				if _purpose == "Value": # we don't actually care about operator/choice fields by themselves
					if value is None or str(value) is "": # ignore empty value data.  django doesn't let you query/filter empty strings.
						# eg, filter(column_name='') will error out.
						# the str() is a hack because u"" != "".  Feels safer to convert to the test than to assume it's unicode
						continue
					else: # this cleaned data has info!
						if _category == 'Related':
							related_q = Q() # create an _different_ Q object, because related objects are first OR'd together, then AND'd with the other fields
							intraAND = data[_index + " " + _category + " intra-Logical"] == 'AND'
							for datum in data[name]: # so for every related object selected
								q_dict = {self.fields[name].field_name: datum} # create the dictionary which we immediately unpack into a Q object
								if intraAND:
									related_q = related_q & Q(**q_dict) # OR the related Q objects together
								else:
									related_q = related_q | Q(**q_dict) # AND the related Q objects together

							extraAND = data[_index + " " + _category + " extra-Logical"] == 'AND'
							if extraAND:
								q_object = q_object & related_q # and then finally AND the related field Q objects with the other fields
							else:
								q_object = q_object | related_q # and then finally OR the related field Q objects with the other fields
						elif _category == 'Bool':
							choice = data[_index + " " + _category + " Choice"]
							q_dict = {choice: value} # create a dict() that looks like {column_name: False}
							logicalAND = data[_index + " " + _category + " Logical"] == 'AND'
							if logicalAND:
								q_object = q_object & Q(**q_dict) # unpack the dict() into a Q(), then AND this with the other fields
							else:
								q_object = q_object | Q(**q_dict) # unpack the dict() into a Q(), then OR this with the other fields
						elif _category == 'Char' or "Num-" in _category:
							choice = data[_index + " " + _category + " Choice"]
							operator = data[_index + " " + _category + " Operator"]
							filter = choice + operator
							q_dict = {filter: value} # create a dict() that looks like {column_name__operator: user_entered_value}
							logicalAND = data[_index + " " + _category + " Logical"] == 'AND'
							if logicalAND:
								q_object = q_object & Q(**q_dict) # unpack the dict() into a Q(), then AND this with the other fields
							else:
								q_object = q_object | Q(**q_dict) # unpack the dict() into a Q(), then OR this with the other fields
						elif _category == 'Discrete':
							# you get the idea
							choice = data[_index + " " + _category + " Choice"]
							q_dict = {choice: value}
							logicalAND = data[_index + " " + _category + " Logical"] == 'AND'
							if logicalAND:
								q_object = q_object & Q(**q_dict) # unpack the dict() into a Q(), then AND this with the other fields
							else:
								q_object = q_object | Q(**q_dict) # unpack the dict() into a Q(), then OR this with the other fields
						else:
							print 'some field i didnt account for in the q builder, but i added in init'
			return q_object # BAM!  Return that sexy Q object
		else: # but only if .is_valid()
			return "Invalid Form."