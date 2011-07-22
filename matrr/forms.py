from django import forms
from django.forms import Form, ModelForm, CharField, widgets, ModelMultipleChoiceField
from django.forms.models import inlineformset_factory
from django.db import transaction
from django.contrib.admin.widgets import FilteredSelectMultiple

import re

from matrr.models import *
from matrr.widgets import *


FIX_CHOICES = (('', '---------'), ('Flash Frozen','Flash Frozen'),
                 ('4% Paraformaldehyde','4% Paraformaldehyde'),
                ('other','other'))

def trim_help_text(text):
  return re.sub(r' Hold down .*$', '', text)


class TissueRequestBaseForm(ModelForm):
  def __init__(self, req_request, tissue, *args, **kwargs):
    self.instance = None
    self.req_request = req_request
    self.tissue = tissue
    super(TissueRequestBaseForm, self).__init__(*args, **kwargs)
    self.fields['monkeys'].widget = CheckboxSelectMultipleLink(link_base='/monkeys/', tissue=self.tissue)
    self.fields['monkeys'].queryset = \
      self.req_request.cohort.monkey_set.all()
    # change the help text to match the checkboxes
    self.fields['monkeys'].help_text = \
      trim_help_text( unicode(self.fields['monkeys'].help_text) )

  def get_request_id(self):
    return self.instance.get_id()


class TissueRequestForm(TissueRequestBaseForm):
  def __init__(self, req_request, tissue, *args, **kwargs):
    super(TissueRequestForm, self).__init__(req_request, tissue, *args, **kwargs)

  def clean(self):
    super(TissueRequestForm, self).clean()
    cleaned_data = self.cleaned_data

    fix_type = cleaned_data.get('rtt_fix_type')
    if self.req_request and \
       self.tissue and \
       fix_type and \
      (self.instance is None or \
       (self.instance.get_id() is not None and\
      self.instance.rtt_fix_type != fix_type )
      ) \
      and \
       TissueRequest.objects.filter( \
        req_request=self.req_request, \
        tissue_type=self.tissue, \
        rtt_fix_type=fix_type).count() > 0:
      raise forms.ValidationError("You already have this tissue and fix in your cart.")

    # Always return the full collection of cleaned data.
    return cleaned_data

  class Meta:
    model = TissueRequest
    exclude = ('req_request', 'tissue_type','accepted_monkeys')
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
    widgets = { 'req_project_title': forms.TextInput(attrs={'size':50})}


class ReviewForm(ModelForm):
  
  def __init__(self, *args, **kwargs):
    TissueRequestReviewFormSet = inlineformset_factory(Review, 
      TissueRequestReview, 
      extra=0, 
      can_delete=False,)
    
    self.peripherals_formset = TissueRequestReviewFormSet(prefix='peripherals', *args, **kwargs)

    BrainRegionRequestReviewFormSet = inlineformset_factory(Review,
      BrainRegionRequestReview,
      extra=0,
      can_delete=False,)

    self.regions_formset = BrainRegionRequestReviewFormSet(prefix='regions', *args, **kwargs)

    CustomTissueRequestReviewFormSet = inlineformset_factory(Review,
                                                             CustomTissueRequestReview,
                                                             extra=0,
                                                             can_delete=False,)

    self.custom_formset = CustomTissueRequestReviewFormSet(prefix='custom', *args, **kwargs)

    super(ReviewForm, self).__init__(*args, **kwargs)
  
  def is_valid(self):
    return self.peripherals_formset.is_valid() \
      and self.regions_formset.is_valid() \
      and self.custom_formset.is_valid() \
      and super(ReviewForm, self).is_valid()

  @transaction.commit_on_success
  def save(self, commit=True):
    super(ReviewForm, self).save(commit)
    self.peripherals_formset.save(commit)
    self.regions_formset.save(commit)
    self.custom_formset.save(commit)
  
  class Meta:
    model = Review


class AccountForm(ModelForm):
  class Meta:
    model = Account


class MtaForm(ModelForm):
  class Meta:
    model = Mta


class BrainRegionRequestForm(TissueRequestBaseForm):
  def clean(self):
    super(BrainRegionRequestForm, self).clean()
    cleaned_data = self.cleaned_data

    if self.req_request and \
       self.tissue and \
       (self.instance is None or \
        self.instance.get_id() is None) \
       and \
       (BrainRegionRequest.objects.filter( \
        req_request=self.req_request, \
        brain_region=self.tissue).count() > 0):
      raise forms.ValidationError("You already have this brain region in your cart.")

    # Always return the full collection of cleaned data.
    return cleaned_data

  class Meta:
    model = BrainRegionRequest
    exclude = ('req_request', 'brain_region','accepted_monkeys')
    widgets = {'rbr_fix_type': FixTypeSelection(choices=FIX_CHOICES)}


class CustomTissueRequestForm(ModelForm):
  def __init__(self, req_request, *args, **kwargs):
    self.instance = None
    self.req_request = req_request
    super(CustomTissueRequestForm, self).__init__(*args, **kwargs)
    self.fields['monkeys'].queryset = \
      self.req_request.cohort.monkey_set.all()

    # change the help text to match the checkboxes
    self.fields['monkeys'].help_text = \
      trim_help_text( unicode(self.fields['monkeys'].help_text) )

  class Meta:
    model = CustomTissueRequest
    exclude = ('req_request','accepted_monkeys')
    widgets = { 'monkeys': CheckboxSelectMultipleLink(link_base='/monkeys/', tissue=None),
                'ctr_fix_type': FixTypeSelection(choices=FIX_CHOICES),}


class ReviewResponseForm(Form):
  subject = CharField(max_length=200, widget=widgets.TextInput(attrs={'size': 130}))
  body = CharField(widget=widgets.Textarea(attrs={'cols': 94,
                                                  'rows': 20}))

  def __init__(self, tissue_requests, *args, **kwargs):
    self.tissue_requests = tissue_requests
    super(ReviewResponseForm, self).__init__( *args, **kwargs )
    for tissue_request in self.tissue_requests:
      if tissue_request.get_tissue():
        self.fields[str(tissue_request)] = ModelMultipleChoiceField(queryset=tissue_request.monkeys.all(),
            required=False,
            widget=GroupedCheckboxSelectMultipleMonkeys(tissue_request=tissue_request)
          )


class ContactUsForm(Form):
  subject = CharField(max_length=200, widget=widgets.TextInput(attrs={'size': 40}))
  body = CharField(widget=widgets.Textarea(attrs={'cols': 40, 'rows': 15}))


class TissueRequestProcessBaseForm(ModelForm):
  def __init__(self, *args, **kwargs):
    super(ModelForm, self).__init__( *args, **kwargs)
    self.fields['accepted_monkeys'].widget = CheckboxSelectMultipleLink(link_base='/monkeys/',
                                                                        tissue=self.instance.get_tissue())
    self.fields['accepted_monkeys'].required = False
    self.fields['accepted_monkeys'].queryset = self.instance.monkeys.all()
    # change the help text to match the checkboxes
    self.fields['accepted_monkeys'].help_text = \
      trim_help_text( unicode(self.fields['accepted_monkeys'].help_text) )


class PeripherialTissueRequestProcessForm(TissueRequestProcessBaseForm):
  class Meta:
    model = TissueRequest
    fields = ('accepted_monkeys',)


class BrainRegionRequestProcessForm(TissueRequestProcessBaseForm):
  class Meta:
    model = TissueRequest
    fields = ('accepted_monkeys',)


class CustomTissueRequestProcessForm(TissueRequestProcessBaseForm):
  class Meta:
    model = CustomTissueRequest
    fields = ('accepted_monkeys',)
    
