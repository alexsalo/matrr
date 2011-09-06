from django import forms
from django.forms import Form, ModelForm, CharField, widgets, ModelMultipleChoiceField
from django.forms.models import inlineformset_factory
from django.db import transaction
from django.contrib.admin.widgets import FilteredSelectMultiple

import re

from matrr.models import *
from matrr.widgets import *


FIX_CHOICES = (('', '---------'), ('Flash Frozen', 'Flash Frozen'),
			   ('4% Paraformaldehyde', '4% Paraformaldehyde'),
			   ('Fresh', 'Fresh'),
			   ('other', 'other'))

def trim_help_text(text):
	return re.sub(r' Hold down .*$', '', text)


class TissueRequestForm(ModelForm):
	def __init__(self, req_request, tissue, *args, **kwargs):
		self.instance = None
		self.req_request = req_request
		self.tissue = tissue
		super(TissueRequestForm, self).__init__(*args, **kwargs)
		self.fields['monkeys'].widget = CheckboxSelectMultipleLink(link_base='/monkeys/', tissue=self.tissue)
		self.fields['monkeys'].queryset =\
		self.req_request.cohort.monkey_set.all()
		# change the help text to match the checkboxes
		self.fields['monkeys'].help_text =\
		trim_help_text(unicode(self.fields['monkeys'].help_text))

	def get_request_id(self):
		return self.instance.rtt_tissue_request_id

	def clean(self):
		super(TissueRequestForm, self).clean()
		cleaned_data = self.cleaned_data

		fix_type = cleaned_data.get('rtt_fix_type')
		if self.req_request and\
		   self.tissue and\
		   fix_type and\
		   (self.instance is None or\
			(self.instance.rtt_tissue_request_id is not None and\
			 self.instance.rtt_fix_type != fix_type )
			   )\
		and\
		   TissueRequest.objects.filter(\
			   req_request=self.req_request,\
			   tissue_type=self.tissue,\
			   rtt_fix_type=fix_type).count() > 0:
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

		return self.cleaned_data

	class Meta:
		model = Request
		exclude = ('request_status')
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
	terms = CharField(label='Search', widget=widgets.TextInput(attrs={'size': 80}))

class ContactUsForm(Form):
	email_subject = CharField(max_length=200, widget=widgets.TextInput(attrs={'size': 40}))
	email_from = EmailField(widget=widgets.TextInput(attrs={'size': 40}))
	email_body = CharField(widget=widgets.Textarea(attrs={'cols': 40, 'rows': 15}))


class TissueRequestProcessForm(ModelForm):
	def __init__(self, *args, **kwargs):
		super(ModelForm, self).__init__(*args, **kwargs)
		self.fields['accepted_monkeys'].widget = CheckboxSelectMultipleLink(link_base='/monkeys/',
																			tissue=self.instance.get_tissue())
		self.fields['accepted_monkeys'].required = False
		self.fields['accepted_monkeys'].queryset = self.instance.monkeys.all()
		# change the help text to match the checkboxes
		self.fields['accepted_monkeys'].help_text =\
		trim_help_text(unicode(self.fields['accepted_monkeys'].help_text))


	class Meta:
		model = TissueRequest
		fields = ('accepted_monkeys',)


class TissueVerificationForm(Form):
	primarykey = IntegerField(widget=HiddenInput(), required=False)
	freezer = CharField(max_length=100, required=False)
	location = CharField(max_length=100, required=False)
	quantity = DecimalField(required=False)
	units = ModelChoiceField(queryset=Unit.objects.all(), required=False)
	details = CharField(widget=widgets.Textarea(attrs={'cols': 70, 'rows': 2}), required=False)
	inventory = ModelChoiceField(queryset=InventoryStatus.objects.all(), required=False)
