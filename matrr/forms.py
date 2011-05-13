from django import forms
from django.forms import Form, ModelForm, CharField, widgets
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
    exclude = ('req_request', 'tissue_type')
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
    exclude = ('req_request', 'brain_region')
    widgets = {'rbr_fix_type': FixTypeSelection(choices=FIX_CHOICES)}


class BloodAndGeneticRequestForm(TissueRequestBaseForm):
  def clean(self):
    super(BloodAndGeneticRequestForm, self).clean()
    cleaned_data = self.cleaned_data

    if self.req_request and \
       self.tissue and \
      (self.instance is None or \
        self.instance.get_id() is None) \
      and \
       (BloodAndGeneticRequest.objects.filter( \
        req_request=self.req_request, \
        blood_genetic_item=self.tissue).count() > 0):
      raise forms.ValidationError("You already have this blood/genetic sample in your cart.")

    # Always return the full collection of cleaned data.
    return cleaned_data

  class Meta:
    model = BloodAndGeneticRequest
    exclude = ('req_request', 'blood_genetic_item')
    widgets = {'rbg_fix_type': FixTypeSelection(choices=FIX_CHOICES)}


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
    exclude = ('req_request',)
    widgets = { 'monkeys': CheckboxSelectMultipleLink(link_base='/monkeys/', tissue=None),
                'ctr_fix_type': FixTypeSelection(choices=FIX_CHOICES),}


class ReviewResponseForm(Form):
  subject = CharField(max_length=200, widget=widgets.TextInput(attrs={'size': 120}))
  body = CharField(widget=widgets.Textarea(attrs={'cols': 86,
                                                  'rows': 10}))


class ContactUsForm(Form):
  subject = CharField(max_length=200, widget=widgets.TextInput(attrs={'size': 40}))
  body = CharField(widget=widgets.Textarea(attrs={'cols': 40, 'rows': 15}))


def remove_values_from_list(the_list, other_list):
   return [value for value in the_list if value not in other_list]

######################################################
# The commented code below here is to serve as a starting point
# for letting a superuser mark tissues as unavailable for
# monkeys when accepting a request.
#
# The original method I was going to use would be to create
# forms for each of the tissues and only show the unavailable_list field.
# I would have also restricted the queryset to only show monkeys involved
# in the request.
#
# This seems to be far more difficult than I originally anticipated,
# so I will instead implement a system where the user gets a
# single checkbox per request to indicate that the monkeys involved
# should be added to the unavailable_list.
# This will push most of the logic into the view and out of the form.
#####################################################
#class TissueTypeUnavailableFormSet(BaseModelFormSet):
#  def __init__(self, tissue_request, *args, **kwargs):
#    self.tissue_request = tissue_request
#    super(TissueTypeUnavailableForm, self).__init__(args, kwargs)
#    self.fields['unavailable_for'].queryset = \
#      self.tissue_request.monkeys.all()
#
#  def save(self):
#    unavailable_list = self.instance.unavailable_list.all()
#    monkey_list = self.tissue_request.monkeys.all()
#    # remove any monkeys in the request from the list
#    unavailable_list = remove_values_from_list(unavailable_list, monkey_list)
#    # add any selected monkeys to the list
#    unavailable_list.extend(Monkey.objects.filter(mky_id__in=self.cleaned_data['']))
#    self.instance.unavailable_list = unavailable_list
#    self.instance.save()
#
#  class Meta:
#    model = TissueRequest
#    exclude = ('tst_type_id','tst_type_name','tst_description','tst_count_per_monkey',)
#    widgets = {
#      'unavailable_for': FilteredSelectMultiple("Monkeys", is_stacked=False)
#    }
#
#class BrainRegionUnavailableForm(ModelForm):
#  class Meta:
#    model = BrainRegion
#    exclude = ('tst_type_id','tst_type_name','tst_description','tst_count_per_monkey',)
#    widgets = {
#      'unavailable_for': FilteredSelectMultiple("Monkeys", is_stacked=False)
#    }
#
#class BloodAndGeneticUnavailableForm(ModelForm):
#  class Meta:
#    model = BloodAndGenetic
#    exclude = ('tst_type_id','tst_type_name','tst_description','tst_count_per_monkey',)
#    widgets = {
#      'unavailable_for': FilteredSelectMultiple("Monkeys", is_stacked=False)
#    }
