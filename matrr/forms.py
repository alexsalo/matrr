#encoding=utf-8
from django import forms
from django.forms import *
from django.forms.extras.widgets import SelectDateWidget
from django.forms.models import inlineformset_factory
from django.db import transaction
from django.contrib.admin.widgets import FilteredSelectMultiple
from datetime import date, timedelta
import re
from matrr.models import *
from matrr import widgets
from registration.forms import RegistrationForm

UPCOMING_FIX_CHOICES = (('', '---------'),
					   ('Flash Frozen', 'Flash Frozen'),
					   ('4% Paraformaldehyde', '4% Paraformaldehyde'),
					   ('Fresh', 'Fresh'),
					   ('other', 'other'))
AVAILABLE_FIX_CHOICES = (('', '---------'),
						('Flash Frozen', 'Flash Frozen'),
						('other', 'other'))
PREP_CHOICES = (('', '---------'),
			   ('DNA', 'DNA'),
			   ('RNA', 'RNA'),
			   ('Tissue', 'Tissue'))


def trim_help_text(text):
	return re.sub(r' Hold down .*$', '', text)
#
#class MonkeySelectForm(Form):
#	monkeys = ModelMultipleChoiceField(queryset = Monkey.objects.all(),required=True, widget=CheckboxSelectMultipleSelectAll())
#
#	def __init__(self, cohort, **kwargs):
#		super(MonkeySelectForm, self).__init__(**kwargs)
#		self.monkeys.queryset = Monkey.objects.filter(cohort=cohort) 


#from django.forms.util import ErrorList
# 
class OtOAcountForm(ModelForm):
	username = CharField(required=False)
	first_name = CharField(required=False)
	last_name = CharField(required=False)
	email = EmailField(required=False)

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
	phone_number = RegexField(regex=r'^[0-9]{10}$', max_length=10, label="Phone number")
	#	address = CharField(label="Address", widget=Textarea(attrs={'cols': '40', 'rows': '5'}), max_length=350)
	act_real_address1 = CharField(label='Address 1', max_length=50, )
	act_real_address2 = CharField(label='Address 2', max_length=50, required=False)
	act_real_city = CharField(label='City', max_length=25, )
	act_real_state = CharField(label='State', max_length=2, )
	act_real_zip = CharField(label='ZIP', max_length=10, )
	act_real_country = CharField(label='Country', max_length=25, required=False)


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
		from matrr.emails import send_verify_new_account_email
		send_verify_new_account_email(account)
		return user


class TissueRequestForm(ModelForm):
	def __init__(self, req_request, tissue, *args, **kwargs):
		def get_fix_choices(req_request):
			if req_request.cohort.coh_upcoming:
				return UPCOMING_FIX_CHOICES
			return AVAILABLE_FIX_CHOICES

		self.Meta.req_request = req_request
		self.instance = None
		self.req_request = req_request
		self.tissue = tissue
		super(TissueRequestForm, self).__init__(*args, **kwargs)
		self.fields['rtt_fix_type'].required = True
		self.fields['rtt_fix_type'].widget = widgets.FixTypeSelection(choices=get_fix_choices(self.req_request))
		self.fields['rtt_prep_type'].required = True
		self.fields['monkeys'].widget = widgets.CheckboxSelectMultipleLinkByTableNoVerification(link_base=self.req_request.cohort.coh_cohort_id,
																						tissue=self.tissue)
		# the first time the form is created the instance does not exist
		if self.instance.pk:
			prev_accepted = self.instance.previously_accepted_monkeys.all().values_list('mky_id', flat=True)
		else:
			prev_accepted = list()
		#		print accepted
		self.fields['monkeys'].queryset = self.req_request.cohort.monkey_set.all().exclude(mky_id__in=prev_accepted)

		# change the help text to match the checkboxes
		self.fields['monkeys'].help_text = trim_help_text(unicode(self.fields['monkeys'].help_text))

	def get_request_id(self):
		return self.instance.rtt_tissue_request_id

	def clean(self):
		super(TissueRequestForm, self).clean()
		cleaned_data = self.cleaned_data

		prep_type = cleaned_data.get('rtt_prep_type')

		# If a user requests DNA/RNA of bone marrow tissue (maybe never), the units will be forced in micrograms, not microliters.  I think this is correct.
		if prep_type == 'DNA' or prep_type == 'RNA':
			if cleaned_data['rtt_units'] != 'ug':
				raise forms.ValidationError("Units of DNA or RNA must be in micrograms.")
		elif "marrow" in self.tissue.tst_tissue_name.lower():
			if cleaned_data['rtt_units'] != 'ul':
				raise forms.ValidationError("Units of bone marrow must be in microliters.")

		rtt_count = TissueRequest.objects.filter(req_request=self.req_request, tissue_type=self.tissue, rtt_prep_type=prep_type).count()
		if self.req_request and self.req_request.req_status != RequestStatus.Revised and self.tissue and prep_type and rtt_count > 0:
			raise forms.ValidationError("You already have this tissue and prep in your cart.")

		# Always return the full collection of cleaned data.
		return cleaned_data

	class Meta:
		model = TissueRequest
		fields = ('rtt_fix_type', 'rtt_prep_type', 'rtt_amount', 'rtt_units', 'rtt_notes', 'monkeys')
		widgets = {'rtt_prep_type': widgets.FixTypeSelection(choices=PREP_CHOICES)}


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
#		exclude = ('req_status', 'req_report_asked', 'req_purchase_order')
		fields = ('req_experimental_plan', 'req_project_title', 'req_reason', 'req_funding', 'req_progress_agreement', 'req_safety_agreement', 'req_referred_by', 'req_notes')
		widgets = {'req_project_title': forms.TextInput(attrs={'size': 50})}


class PurchaseOrderForm(ModelForm):
	class Meta:
		model = Request
		fields = ('req_purchase_order',)


class TrackingNumberForm(ModelForm):
	class Meta:
		model = Shipment
		fields = ('shp_tracking',)


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
		fields = ['act_shipping_name', 'act_fedex', 'act_country', 'act_zip', 'act_state', 'act_city', 'act_address2', 'act_address1']


class AddressAccountForm(ModelForm):
	class Meta:
		model = Account
		fields = ['act_real_address1', 'act_real_address2', 'act_real_city', 'act_real_zip', 'act_real_country', 'act_real_state']


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


class AccountMTAForm(Form):
	institution = ModelChoiceField(queryset=Institution.objects.all(), initial=Institution.objects.get(ins_institution_name='Non-UBMTA Institution'))


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
		self.fields['req_request'].queryset = Request.objects.filter(user=user, req_status=RequestStatus.Shipped)

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
																			widget=widgets.GroupedCheckboxSelectMultipleMonkeys(
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
		self.fields['accepted_monkeys'].widget = widgets.CheckboxSelectMultipleLinkByTable(link_base=self.instance.req_request.cohort.coh_cohort_id,
																				   tissue=self.instance.get_tissue(),
																				   tis_request=self.instance)
		self.fields['accepted_monkeys'].required = False
		self.fields['accepted_monkeys'].queryset = self.instance.monkeys.all()
		# change the help text to match the checkboxes
		self.fields['accepted_monkeys'].help_text = ''

#	def save(self, commit=True):
#		import pdb
#		pdb.set_trace()
#		super(TissueRequestProcessForm, self).save(commit)


	class Meta:
		model = TissueRequest
		fields = ('accepted_monkeys',)


class TissueInventoryVerificationForm(Form):
	primarykey = IntegerField(widget=HiddenInput(), required=False)
	inventory = ChoiceField(choices=InventoryStatus, required=False, widget=widgets.RadioSelect(renderer=widgets.HorizRadioRenderer))


class TissueInventoryVerificationShippedForm(Form):
	primarykey = IntegerField(widget=HiddenInput(), required=False)
	quantity = FloatField(required=False)
	units = ChoiceField(choices=Units, required=False)


class TissueInventoryVerificationDetailForm(TissueInventoryVerificationForm):
	freezer = CharField(max_length=100, required=False)
	location = CharField(max_length=100, required=False)
	quantity = FloatField(required=False)
	units = ChoiceField(choices=Units, required=False)
	details = CharField(widget=widgets.Textarea(attrs={'cols': 40, 'rows': 2, 'style':"width:100%;",}), required=False)


class MTAValidationForm(Form):
	primarykey = IntegerField(widget=HiddenInput(), required=False)
	is_valid = BooleanField(required=False)


class DateRangeForm(Form):
	from_date = DateField(widget=widgets.DateTimeWidget, required=False)
	to_date = DateField(widget=widgets.DateTimeWidget, required=False)

	def __init__(self, min_date=None, max_date=None, *args, **kwargs):
		super(DateRangeForm, self).__init__(*args, **kwargs)
		self.fields['from_date'].widget.attrs['min_date'] = min_date
		self.fields['from_date'].widget.attrs['max_date'] = max_date
		self.fields['to_date'].widget.attrs['min_date'] = min_date
		self.fields['to_date'].widget.attrs['max_date'] = max_date


class FilterForm(Form):
	"""
	This form creates 3(ish) fields for every model field passed into it.  This allows the user to choose which field to filter, which operator to filter
	with, and value to filter.  FilterForm.get_q_object() will create and return a Q object from the filled out form fields.  In the view you pass
	this into the chosen model's filter method.

	eg:
	filter_form=FilterForm(Monkey._meta.fields)
	<user input>
	filter_form=FilterForm(Monkey._meta.fields, data=request.POST)
	Monkey.objects.filter(filter_form.get_q_object())
	"""
	NUMERIC_OPERATORS = (
	("__gte", "greater than or equal to"),
	("__lte", "less than or equal to"),
	("__gt", "greater than"),
	("__lt", "less than"),
	("", "equal to"),
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
			self.fields[i + ' Num-Int Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=widgets.HorizRadioRenderer,
																										   choices=(('AND', 'AND'), ('OR', 'OR'))), initial="AND")
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
			self.fields[i + ' Num-Float Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=widgets.HorizRadioRenderer,
																											 choices=(('AND', 'AND'), ('OR', 'OR'))), initial="AND")
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
			self.fields[i + ' Char Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=widgets.HorizRadioRenderer,
																										choices=(('AND', 'AND'), ('OR', 'OR'))), initial="AND")
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
			self.fields[i + ' Bool Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=widgets.HorizRadioRenderer,
																										choices=(('AND', 'AND'), ('OR', 'OR'))), initial="AND")
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
			self.fields[i + ' Discrete Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=widgets.HorizRadioRenderer,
																											choices=(('AND', 'AND'), ('OR', 'OR'))), initial="AND")
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
			self.fields[i + ' Related extra-Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=widgets.HorizRadioRenderer,
																												 choices=(('AND', 'AND'), ('OR', 'OR'))), initial="AND")
			self.fields[i + ' Related extra-Logical'].label = "Relation %s extra-Combine" % i
			self.fields[i + ' Related extra-Logical'].help_text = "AND this field with the other fields or OR them together."
			self.fields[i + ' Related intra-Logical'] = forms.CharField(required=False, widget=forms.RadioSelect(renderer=widgets.HorizRadioRenderer,
																												 choices=(('AND', 'AND'), ('OR', 'OR'))), initial="OR")
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


class SubjectSelectForm(Form):
	def __init__(self, subject_label='', subject_helptext='', subject_queryset=None, subject_widget=None, horizontal=False, *args, **kwargs):
		# This was hacked together in a couple stages, so its sorta silly.
		# The horizontal kwarg will assign subject.widget to horizontally-aligned RadioSelect
		# The subject_widget kwarg will assign the widget for the subject field to whatever is passed in.
		# horizontal will completely ignore subject_widget
		# subject_widget kwarg will override the horizontal kwarg
		super(Form, self).__init__(*args, **kwargs)
		queryset = subject_queryset if subject_queryset else Cohort.objects.all()
		widget = widgets.RadioSelect(renderer=widgets.HorizRadioRenderer) if horizontal else RadioSelect(renderer=widgets.RadioRenderer_nolist)
		widget = subject_widget if subject_widget else widget
		self.fields['subject'] = ModelChoiceField(queryset=queryset.order_by('pk'), widget=widget, initial=queryset[0])
		self.fields['subject'].label = subject_label if subject_label else "Subject"
		self.fields['subject'].help_text = subject_helptext if subject_helptext else "Select a Subject"



class CohortSelectForm(SubjectSelectForm):
	def __init__(self, *args, **kwargs):
		super(CohortSelectForm, self).__init__(subject_label='Cohort', subject_helptext='Select a cohort', *args, **kwargs)


class MonkeySelectForm(SubjectSelectForm):
	def __init__(self, 	*args, **kwargs):
		super(MonkeySelectForm, self).__init__(subject_label='Monkey', subject_helptext='Select a monkey', *args, **kwargs)


class GenealogyParentsForm(MonkeySelectForm):
	def __init__(self, *args, **kwargs):
		super(GenealogyParentsForm, self).__init__(*args, **kwargs)
		self.fields['father'] = ModelChoiceField(queryset=Monkey.objects.filter(mky_gender='M').order_by('pk'))
		self.fields['father'].label = "Father"
		self.fields['father'].help_text = "Select monkey's father"

		self.fields['mother'] = ModelChoiceField(queryset=Monkey.objects.filter(mky_gender='F').order_by('pk'))
		self.fields['mother'].label = "Mother"
		self.fields['mother'].help_text = "Select monkey's mother"


class RNALandingForm(CohortSelectForm):
	yields_choices = (('submit', 'Submit RNA yields'), ('display', "Display RNA yields"))
	yields = ChoiceField(choices=yields_choices, label="", widget=widgets.RadioSelect, required=True,
						 help_text="Do you want to upload or display RNA yields for the selected cohort?", )
	def __init__(self, *args, **kwargs):
		super(RNALandingForm, self).__init__(subject_widget=widgets.Select, *args, **kwargs)


class RNASubmitForm(ModelForm):
	cohort = None
	def __init__(self, cohort, *args, **kwargs):
		super(ModelForm, self).__init__(*args, **kwargs)
		self.cohort = cohort
		self.fields['monkey'].queryset = cohort.monkey_set.all()
		self.fields['monkey'].required = False

	class Meta:
		model = RNARecord
		fields = ('tissue_type', 'monkey', 'rna_min', 'rna_max')


class ProteinSelectForm(Form):
	def __init__(self, protein_queryset=None, columns=3, *args, **kwargs):
		super(ProteinSelectForm, self).__init__(*args, **kwargs)
		self.queryset = protein_queryset if protein_queryset else Protein.objects.all()
		self.fields['proteins'] = ModelMultipleChoiceField(queryset=self.queryset, widget=widgets.CheckboxSelectMultiple_columns(columns=columns))
		self.fields['proteins'].label = "Protein"
		self.fields['proteins'].help_text = "Select proteins to display"


class ProteinSelectForm_advSearch(ProteinSelectForm):
	def __init__(self, columns=1, *args, **kwargs):
		super(ProteinSelectForm_advSearch, self).__init__(*args, **kwargs)
		self.fields['proteins'].widget = widgets.CheckboxSelectMultiple_proteinAdvSearch(columns=columns, queryset=self.queryset)

class MonkeyProteinGraphAppearanceForm(Form):
	y_choices = (('monkey_protein_pctdev', 'Percent deviation from cohort mean'), ('monkey_protein_stdev',
				 'Standard deviation from cohort mean'), ('monkey_protein_value', 'Actual value'))
	yaxis_units = ChoiceField(choices = y_choices, label='Y axis', help_text="Select data to display on y axis",
							initial=y_choices[2][0])
	filter_choices = (('all', 'All values'), ('morning','Only values collected before noon'), ('afternoon', 'Only values collected after noon'))
	data_filter = ChoiceField(choices = filter_choices, label="Data filter", help_text="Limit data to display based on time of day collected",
							initial=filter_choices[0][0])
	monkeys = CharField(widget=HiddenInput())
	def __init__(self, monkeys=None, *args, **kwargs):
		super(MonkeyProteinGraphAppearanceForm, self).__init__(*args, **kwargs)
		if monkeys:
			self.fields['monkeys'].initial = monkeys


class DataSelectForm(Form):
	dataset_choices = (('protein', 'Access protein-associated data tools'), ('etoh', 'Access ethanol-associated data tools'))
	dataset = ChoiceField(choices=dataset_choices, label='Data Set', help_text="Choose what data to analyze", widget=RadioSelect, initial=dataset_choices[0][0])

#fiels = document.getElementByID('monkey_fieldset'); fiels.style.display='None';
class GraphSubjectSelectForm(Form):
	subject_choices = (('cohort', 'Cohorts'), ('monkey', 'Monkeys'), ('download', 'Download all data'))
	subject = ChoiceField(choices=subject_choices,
						  label='Subject',
						  help_text="Choose what scope of subjects to analyze",
						  widget=RadioSelect(renderer=widgets.RadioFieldRendererSpecial_monkey),
						  initial=subject_choices[0][0])
	monkeys = ModelMultipleChoiceField(queryset=Monkey.objects.all(), required=False, widget=widgets.CheckboxSelectMultipleSelectAll())

	def __init__(self, monkey_queryset, **kwargs):
		super(GraphSubjectSelectForm, self).__init__(**kwargs)
		self.fields['monkeys'].queryset = monkey_queryset


class TissueShipmentForm(Form):
	def __init__(self, tissue_request_queryset, *args, **kwargs):
		super(TissueShipmentForm, self).__init__(*args, **kwargs)
		self.fields['tissue_requests'] = ModelMultipleChoiceField(queryset=tissue_request_queryset, widget=widgets.CheckboxSelectMultiple_columns(columns=2))
		self.fields['tissue_requests'].label = "Shipment"
		self.fields['tissue_requests'].help_text = "Select which tissue requests are included in this shipment"


class PlotSelectForm(Form):
	plot_method = ChoiceField(help_text="Choose which plot to generate")

	def __init__(self, plot_choices, **kwargs):
		super(PlotSelectForm, self).__init__(**kwargs)
		self.fields['plot_method'].label = "Plot"
		self.fields['plot_method'].choices = plot_choices
		self.fields['plot_method'].initial = plot_choices[0][0]


class ExperimentRangeForm(Form):
	range_choices = (('Induction', 'Induction'), ('Open Access', 'Open Access'), ('custom', 'Custom Dates'))
	range = ChoiceField(choices=range_choices,
						  label='Experiment Range',
						  help_text="Choose which dates to analyze",
						  widget=RadioSelect(renderer=widgets.RadioFieldRendererSpecial_dates),
						  initial=range_choices[0][0])
	from_date = DateField(widget=widgets.DateTimeWidget, required=False)
	to_date = DateField(widget=widgets.DateTimeWidget, required=False)


class ExperimentRangeForm_monkeys(ExperimentRangeForm):
	monkeys = CharField(widget=HiddenInput())
	def __init__(self, monkeys=None, *args, **kwargs):
		super(ExperimentRangeForm_monkeys, self).__init__(*args, **kwargs)
		if monkeys:
			self.fields['monkeys'].initial = monkeys

class BECRangeForm(ExperimentRangeForm):
	sample_choices = (('all', 'All Samples'), ('morning', 'Sampled before 2pm'), ('afternoon', 'Sampled After 2pm'))
	sample_range = ChoiceField(choices=sample_choices,
							   label='Time of blood sample',
							   help_text="Blood samples were taken at multiple times of day, generally 11a-1p and 3p-5p.",
							   widget=RadioSelect(renderer=widgets.RadioFieldRendererSpecial_dates),
							   initial=sample_choices[0][0])


class BECRangeForm_monkeys(BECRangeForm): # same as ExperimentRangeForm_monkeys, except for the parent class
	monkeys = CharField(widget=HiddenInput())
	def __init__(self, monkeys=None, *args, **kwargs):
		super(BECRangeForm_monkeys, self).__init__(*args, **kwargs)
		if monkeys:
			self.fields['monkeys'].initial = monkeys


class AdvancedSearchSelectForm(Form):
	sex = MultipleChoiceField(choices=Monkey.SEX_CHOICES, required=False, widget=widgets.CheckboxSelectMultiple(attrs={'onchange': 'post_adv_form()'}))
	species = MultipleChoiceField(choices=Monkey.SPECIES, required=False, widget=widgets.CheckboxSelectMultiple(attrs={'onchange': 'post_adv_form()'}))


class AdvancedSearchFilterForm(Form):
	control = BooleanField(label="Control", required=False, widget=widgets.CheckboxInput(attrs={'onchange': 'post_adv_form()'}))
	proteins = ModelMultipleChoiceField(label="Proteins", required=False, queryset=Protein.objects.all(), widget=widgets.CheckboxSelectMultiple_columns(columns=1, attrs={'onchange': 'post_adv_form()'}))
	cohorts = ModelMultipleChoiceField(label="Cohorts", required=False, queryset=Cohort.objects.all(), widget=widgets.CheckboxSelectMultiple_columns(columns=1, attrs={'onchange': 'post_adv_form()'}))


class InventoryBrainForm(Form):
	block_names = MonkeyBrainBlock.objects.all().order_by().values_list('mbb_block_name', flat=True).distinct().order_by('mbb_block_name')
	BLOCKS = tuple((name, name) for name in block_names)

	block = ChoiceField(choices=BLOCKS, required=True)
	left_tissues = ModelMultipleChoiceField(queryset=TissueType.objects.filter(category__cat_name__icontains='brain').order_by('tst_tissue_name'), required=False, widget=widgets.CheckboxSelectMultiple_columns(columns=1))
	right_tissues = ModelMultipleChoiceField(queryset=TissueType.objects.filter(category__cat_name__icontains='brain').order_by('tst_tissue_name'), required=False, widget=widgets.CheckboxSelectMultiple_columns(columns=1))

