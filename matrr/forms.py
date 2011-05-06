from django import forms
from django.forms import ModelForm
from django.forms.models import inlineformset_factory
from django.db import transaction

import re

from matrr.models import *
from matrr.widgets import *

def trim_help_text(text):
  return re.sub(r' Hold down .*$', '', text)


class TissueRequestBaseForm(ModelForm):
  def __init__(self, req_request, tissue, *args, **kwargs):
    self.instance = None
    self.req_request = req_request
    self.tissue = tissue
    super(TissueRequestBaseForm, self).__init__(*args, **kwargs)
    self.fields['monkeys'].queryset = \
      self.req_request.cohort.monkey_set.all()

    # change the help text to match the checkboxes
    self.fields['monkeys'].help_text = \
      trim_help_text( unicode(self.fields['monkeys'].help_text) )

  def get_request_id(self):
    return self.instance.get_id()

  class Meta:
    widgets = { 'monkeys': CheckboxSelectMultipleLink(link_base='/monkeys/') }

class TissueRequestForm(TissueRequestBaseForm):
  def __init__(self, req_request, tissue, *args, **kwargs):
    super(TissueRequestForm, self).__init__(req_request, tissue, *args, **kwargs)
    self.fields['fix_type'].queryset = \
      self.tissue.fixes.all()

  def clean(self):
    super(TissueRequestForm, self).clean()
    cleaned_data = self.cleaned_data

    fix_type = cleaned_data.get('fix_type')
    if self.req_request and \
       self.tissue and \
       fix_type and \
      (self.instance is None or \
       (self.instance.get_id() is not None and\
      self.instance.fix_type != fix_type )
      ) \
      and \
       TissueRequest.objects.filter( \
        req_request=self.req_request, \
        tissue_type=self.tissue, \
        fix_type=fix_type).count() > 0:
      raise forms.ValidationError("You already have this tissue and fix in your cart.")

    # Always return the full collection of cleaned data.
    return cleaned_data

  class Meta:
    model = TissueRequest
    exclude = ('req_request', 'tissue_type')
    widgets = { 'monkeys': CheckboxSelectMultipleLink(link_base='/monkeys/') }


class CartCheckoutForm(ModelForm):
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

    BloodAndGeneticRequestReviewFormSet = inlineformset_factory(Review,
      BloodAndGeneticRequestReview,
      extra=0,
      can_delete=False,)

    self.samples_formset = BloodAndGeneticRequestReviewFormSet(prefix='samples', *args, **kwargs)

    CustomTissueRequestReviewFormSet = inlineformset_factory(Review,
                                                             CustomTissueRequestReview,
                                                             extra=0,
                                                             can_delete=False,)

    self.custom_formset = CustomTissueRequestReviewFormSet(prefix='custom', *args, **kwargs)

    super(ReviewForm, self).__init__(*args, **kwargs)
  
  def is_valid(self):
    return self.peripherals_formset.is_valid() \
      and self.regions_formset.is_valid() \
      and self.samples_formset.is_valid() \
      and self.custom_formset.is_valid() \
      and super(ReviewForm, self).is_valid()

  @transaction.commit_on_success
  def save(self, commit=True):
    super(ReviewForm, self).save(commit)
    self.peripherals_formset.save(commit)
    self.regions_formset.save(commit)
    self.samples_formset.save(commit)
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
       (self.instance is not None and \
        self.instance.get_id() is not None) \
       or \
       (BrainRegionRequest.objects.filter( \
        req_request=self.req_request, \
        brain_region=self.tissue).count() > 0):
      raise forms.ValidationError("You already have this brain region in your cart.")

    # Always return the full collection of cleaned data.
    return cleaned_data

  class Meta:
    model = BrainRegionRequest
    exclude = ('req_request', 'brain_region')
    widgets = { 'monkeys': CheckboxSelectMultipleLink(link_base='/monkeys/') }


class BloodAndGeneticRequestForm(TissueRequestBaseForm):
  def clean(self):
    super(BloodAndGeneticRequestForm, self).clean()
    cleaned_data = self.cleaned_data

    if self.req_request and \
       self.tissue and \
      (self.instance is not None and \
        self.instance.get_id() is not None) \
      or \
       (BloodAndGeneticRequest.objects.filter( \
        req_request=self.req_request, \
        blood_genetic_item=self.tissue).count() > 0):
      raise forms.ValidationError("You already have this blood/genetic sample in your cart.")

    # Always return the full collection of cleaned data.
    return cleaned_data

  class Meta:
    model = BloodAndGeneticRequest
    exclude = ('req_request', 'blood_genetic_item')
    widgets = { 'monkeys': CheckboxSelectMultipleLink(link_base='/monkeys/') }

