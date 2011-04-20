from django import forms
from django.forms import ModelForm
from django.forms.models import inlineformset_factory

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


class ReviewForm(ModelForm):
  
  def __init__(self, *args, **kwargs):
    TissueRequestReviewFormSet = inlineformset_factory(Review, 
      TissueRequestReview, 
      extra=0, 
      can_delete=False,)
    
    self.peripherals_formset = TissueRequestReviewFormSet(prefix='peripherals', *args, **kwargs)

    BrainBlockRequestReviewFormSet = inlineformset_factory(Review,
      BrainBlockRequestReview,
      extra=0,
      can_delete=False,)

    self.blocks_formset = BrainBlockRequestReviewFormSet(prefix='blocks', *args, **kwargs)

    BrainRegionRequestReviewFormSet = inlineformset_factory(Review,
      BrainRegionRequestReview,
      extra=0,
      can_delete=False,)

    self.regions_formset = BrainRegionRequestReviewFormSet(prefix='regions', *args, **kwargs)

    MicrodissectedRegionRequestReviewFormSet = inlineformset_factory(Review,
      MicrodissectedRegionRequestReview,
      extra=0,
      can_delete=False,)

    self.microdissected_formset = MicrodissectedRegionRequestReviewFormSet(prefix='microdissected', *args, **kwargs)

    BloodAndGeneticRequestReviewFormSet = inlineformset_factory(Review,
      BloodAndGeneticRequestReview,
      extra=0,
      can_delete=False,)

    self.samples_formset = BloodAndGeneticRequestReviewFormSet(prefix='samples', *args, **kwargs)

    super(ReviewForm, self).__init__(*args, **kwargs)
  
  def is_valid(self):
    return self.peripherals_formset.is_valid() \
      and self.blocks_formset.is_valid() \
      and self.regions_formset.is_valid() \
      and self.microdissected_formset.is_valid() \
      and self.samples_formset.is_valid() \
      and super(ReviewForm, self).is_valid()
    
  def save(self, commit=True):
    super(ReviewForm, self).save(commit)
    self.peripherals_formset.save(commit)
    self.blocks_formset.save(commit)
    self.regions_formset.save(commit)
    self.microdissected_formset.save(commit)
    self.samples_formset.save(commit)
  
  class Meta:
    model = Review


class AccountForm(ModelForm):
  class Meta:
    model = Account

class MtaForm(ModelForm):
  class Meta:
    model = Mta


class BrainBlockRequestForm(TissueRequestBaseForm):
  def clean(self):
    super(BrainBlockRequestForm, self).clean()
    cleaned_data = self.cleaned_data

    if self.req_request and \
       self.tissue and \
       BrainBlockRequest.objects.filter( \
        req_request=self.req_request, \
        brain_block=self.tissue).count() > 0:
      raise forms.ValidationError("You already have this brain block in your cart.")

    # Always return the full collection of cleaned data.
    return cleaned_data

  class Meta:
    model = BrainBlockRequest
    exclude = ('req_request', 'brain_block')
    widgets = { 'monkeys': CheckboxSelectMultipleLink(link_base='/monkeys/') }


class BrainRegionRequestForm(TissueRequestBaseForm):
  def clean(self):
    super(BrainRegionRequestForm, self).clean()
    cleaned_data = self.cleaned_data

    if self.req_request and \
       self.tissue and \
       BrainRegionRequest.objects.filter( \
        req_request=self.req_request, \
        brain_region=self.tissue).count() > 0:
      raise forms.ValidationError("You already have this brain region in your cart.")

    # Always return the full collection of cleaned data.
    return cleaned_data

  class Meta:
    model = BrainRegionRequest
    exclude = ('req_request', 'brain_region')
    widgets = { 'monkeys': CheckboxSelectMultipleLink(link_base='/monkeys/') }


class MicrodissectedRegionRequestForm(TissueRequestBaseForm):
  def clean(self):
    super(MicrodissectedRegionRequestForm, self).clean()
    cleaned_data = self.cleaned_data

    if self.req_request and \
       self.tissue and \
       MicrodissectedRegionRequest.objects.filter( \
        req_request=self.req_request, \
        microdissected_region=self.tissue).count() > 0:
      raise forms.ValidationError("You already have this microdissected region in your cart.")

    # Always return the full collection of cleaned data.
    return cleaned_data

  class Meta:
    model = MicrodissectedRegionRequest
    exclude = ('req_request', 'microdissected_region')
    widgets = { 'monkeys': CheckboxSelectMultipleLink(link_base='/monkeys/') }


class BloodAndGeneticRequestForm(TissueRequestBaseForm):
  def clean(self):
    super(BloodAndGeneticRequestForm, self).clean()
    cleaned_data = self.cleaned_data

    if self.req_request and \
       self.tissue and \
       BloodAndGeneticRequest.objects.filter( \
        req_request=self.req_request, \
        blood_genetic_item=self.tissue).count() > 0:
      raise forms.ValidationError("You already have this blood/genetic sample in your cart.")

    # Always return the full collection of cleaned data.
    return cleaned_data

  class Meta:
    model = BloodAndGeneticRequest
    exclude = ('req_request', 'blood_genetic_item')
    widgets = { 'monkeys': CheckboxSelectMultipleLink(link_base='/monkeys/') }

