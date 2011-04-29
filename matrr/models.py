from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime

from djangosphinx.models import SphinxSearch

# this is a snippet from http://djangosnippets.org/snippets/1683/
# it will allow me to monitor some classes to see when they change state
class DiffingMixin(object):
  def __init__(self):
    super(DiffingMixin, self).__init__()
    self._original_state = dict(self.__dict__)
  def save(self, *args, **kwargs):
    state = dict(self.__dict__)
    del state['_original_state']
    self._original_state = state
    #super(DiffingMixin, self).save()
  def is_dirty(self):
    missing = object()
    for key, value in self._original_state.iteritems():
      if value != self.__dict__.get(key, missing):
        return True
    return False
  def changed_columns(self):
    missing = object()
    result = {}
    for key, value in self._original_state.iteritems():
      if value != self.__dict__.get(key, missing):
        result[key] = {'old':value, 'new':self.__dict__.get(key, missing)}
    return result


class Institution(models.Model):
  ins_institution_id = models.AutoField('ID', primary_key=True)
  ins_institution_name = models.CharField('Institution', max_length=100, unique=True, null=False,
                                     help_text='Please enter the name of the institution.')

  def __unicode__(self):
    return self.ins_institution_name

  class Meta:
    db_table = 'ins_institutions'



class EventType(models.Model):
  evt_id = models.AutoField('ID', primary_key=True)
  evt_name = models.CharField('Name', max_length=100, unique=True, null=False,
                              help_text='The name of the event.')
  evt_description = models.TextField('Description', null=True, blank=True,
                                     help_text='A description of the event.')

  def __unicode__(self):
    return self.evt_name

  class Meta:
    db_table = 'evt_event_types'


class Cohort(models.Model):
  coh_cohort_id = models.AutoField('ID', primary_key=True)
  coh_cohort_name = models.CharField('Name', max_length=100, unique=True, null=False,
                                     help_text='Please enter the cohort\'s name')
  coh_upcoming = models.BooleanField('Upcoming', null=False, default=True,
                                     help_text='Check this if the tissues from this cohort have not been harvested yet.')
  institution = models.ForeignKey(Institution, related_name='cohort_set', db_column='ins_institution_id',
                                  verbose_name='Institution',
                                  help_text='Please select the institution where this cohort was raised.')
  events = models.ManyToManyField(EventType, through='CohortEvent', related_name='cohort_set')
  coh_species = models.CharField('Species', max_length=30,
                                 help_text='Please enter the species of the monkeys in this cohort.')
  
  def __unicode__(self):
    return self.coh_cohort_name
  
  def get_url(self):
    url = '/'
    if self.coh_upcoming:
      url += 'upcoming'
    else:
      url += 'available'
    url += '/' + str(self.coh_cohort_id) + '/'
    return url
  
  class Meta:
    db_table = 'coh_cohorts'


class CohortEvent(models.Model):
  cev_id = models.AutoField(primary_key=True)
  cohort = models.ForeignKey(Cohort, related_name='cohort_event_set', db_column='coh_cohort_id',
                             verbose_name='Cohort',
                             help_text='The cohort this event is for.')
  event = models.ForeignKey(EventType, related_name='cohort_event_set', db_column='evt_id',
                            verbose_name='Event Type',
                            help_text='The type of event.')
  cev_date = models.DateField('Date',
                              help_text='The date of this event.')
  cev_info = models.CharField('Additional Info', max_length=200,
                              blank=True, null=True,
                              help_text='This is for entering some additional info for the event. There is a 200 character limit.')

  def __unicode__(self):
    return str(self.cohort) + ' ' + str(self.event)

  class Meta:
    db_table = 'cev_cohort_events'


class Monkey(models.Model):
  GENDER_CHOICES = (
    ('M', 'Male'),
    ('F', 'Female'),
  )
  mky_id = models.AutoField('Internal ID', primary_key=True)
  cohort = models.ForeignKey(Cohort, db_column='coh_cohort_id', verbose_name='Cohort',
                             help_text='The cohort this monkey belongs to.')
  mky_real_id = models.IntegerField('ID', unique=True, null=False,
                                    help_text='The ID of the monkey.')
  mky_name = models.CharField('Name', max_length=100, blank=True, null=True,
                              help_text='The monkey\'s name.')
  mky_gender = models.CharField('Gender', max_length=1, choices=GENDER_CHOICES, blank=True, null=True,
                               help_text='The sex of the monkey.')
  mky_birthdate = models.CharField('Date of Birth', blank=True, null=True,
                                   max_length=20,
                                   help_text='Please enter the date the monkey was born on.')
  mky_weight = models.IntegerField('Weight', blank=True, null=True,
                                   help_text='The weight of the monkey.  This should be the weight at time of necropsy (or a recent weight if the necropsy has not yet occurred).')
  mky_drinking = models.BooleanField('Drinking', null=False,
                                     help_text='Was this monkey given alcohol?')
  mky_necropsy_date = models.DateField('Necropsy Date', null=True, blank=True,
                                       help_text='Please enter the date the necropsy was performed on.')
  mky_study_complete = models.BooleanField('Complete Study Performed', null=False,
                                           default=False,
                                           help_text='Did this monkey complete all stages of the experiment?')
  mky_stress_model = models.CharField('Stress Model', null=True, blank=True,
                                      max_length=30,
                                      help_text='This should indicate the grouping of the monkey if it was in a cohort that also tested stress models. (ex. MR, NR, HC, LC) ')
    
  def __unicode__(self):
    return str(self.mky_real_id)
  
  class Meta:
    db_table = 'mky_monkeys'


class Mta(models.Model):
  mta_id = models.AutoField(primary_key=True)
  user = models.ForeignKey(User, related_name='mta_set', db_column='usr_id', editable=False, blank=True)
  mta_date = models.DateField('Date Uploaded', editable=False, blank=True, null=True, help_text='This is the Date that the MTA is uploaded.')
  mta_title = models.CharField('Title', blank=True, null=False, max_length=25, help_text='Give your uploaded MTA a short unique name to make it easier for you to reference')
  mta_file = models.FileField(upload_to='mta/', default='', null=False, blank=False, help_text='File to Upload')
  
  def __unicode__(self):
    return str(self.mta_id)

  def save(self, force_insert=False, force_update=False, using=None):
    self.mta_date = datetime.now()
    if self.mta_title is None:
      self.mta_title = self.mta_file.name
    super(Mta, self).save(force_insert, force_update, using)
    
  class Meta:
    db_table = 'mta_material_transfer'
    

class Account(models.Model):
  user = models.OneToOneField(User, related_name='account', db_column='usr_usr_id', editable=False, blank=True, primary_key=True)
  act_shipping_name = models.CharField(max_length=25, null=True, blank=True, help_text="Your shipping name is required because it may be different from your username.")
  act_address1 = models.CharField(max_length=50, null=True, blank=True)
  act_address2 = models.CharField(max_length=50, null=True, blank=True)
  act_city = models.CharField(max_length=25, null=True, blank=True)
  act_state = models.CharField(max_length=2, null=True, blank=True)
  act_zip = models.CharField(max_length=10, null=True, blank=True)
  act_country = models.CharField(max_length=25, null=True, blank=True)
  act_fedex = models.CharField('FedEx', max_length=9, null=True, blank=True, help_text="Your 9-digit FedEx Account number is required to ship tissues.")

  def __unicode__(self):
    return str(self.user.id)
   
  class Meta:
    db_table = 'act_account'


class DrinkingExperiment(models.Model):
  dex_id = models.AutoField('ID', primary_key=True)
  cohort = models.ForeignKey(Cohort, related_name='cohort_drinking_experiment_set', db_column='coh_cohort_id',
                             verbose_name='Cohort',
                             help_text='The cohort this experiment was performed on.')
  #dex_name = models.CharField(max_length=100, unique=True, null=False)
  #dex_description = models.TextField(null=True, blank=True)
  dex_date = models.DateField('Date',
                              help_text='The date this experiment was conducted.')
  dex_type = models.CharField('Experiment Type', max_length=100,
                              help_text='The type of experiment. (ex. 22 hour free access)')
  dex_notes = models.TextField('Notes', blank=True, null=True,
                               help_text='Use this space to enter anything about the experiment that does not fit in another field.')
  monkeys = models.ManyToManyField(Monkey, through='MonkeyToDrinkingExperiment')
  
  def __unicode__(self):
    return 'Experiment Type: ' + self.dex_type + ' Date: ' + str(self.dex_date) + ' Cohort: ' + str(self.cohort)
  
  def save(self, force_insert=False, force_update=False, using=None):
    is_new = False
    if self.dex_id is None:
      is_new = True
    super(DrinkingExperiment, self).save(force_insert, force_update, using)
    
    if is_new:
      # on INSERT, create new MonkeyToExperiment instances
      for monkey in self.cohort.monkey_set.all():
        # create a new MonkeyToExperiment instance for each monkey in the cohort
        MonkeyToDrinkingExperiment(monkey=monkey, drinking_experiment=self).save()
  
  class Meta:
    db_table = 'dex_drinking_experiments'


class MonkeyToDrinkingExperiment(models.Model):
  mtd_id = models.AutoField(primary_key=True)
  monkey = models.ForeignKey(Monkey, null=False, related_name='+', db_column='mky_id', editable=False)
  drinking_experiment = models.ForeignKey(DrinkingExperiment, null=False, related_name='+', db_column='dex_id', editable=False)
  mtd_etoh_intake = models.FloatField('EtOH Intake', null=True, blank=True,
                                      help_text='Please enter the amount in mL of 4% EtOH consumed by the monkey.')
  mtd_veh_intake = models.FloatField('H2O Intake', null=True, blank=True,
                                      help_text='Please enter the amount in mL of H2O consumed by the monkey.')
  mtd_total_pellets = models.IntegerField('Pellets Consumed', null=True, blank=True,
                                          help_text='Please enter the total number of pellets consumed by the monkey.')
  mtd_weight = models.FloatField('Weight', null=True, blank=True,
                                 help_text='Please enter the weight of the monkey.')
  mtd_notes = models.TextField('Notes', blank=True, null=True,
                               help_text='Use this space to enter anything about the experiment that does not fit in another field.')
  
  def __unicode__(self):
    return str(self.drinking_experiment) + ' Monkey: ' + str(self.monkey)
  
  def get_etoh_ratio(self):
    return self.mtd_etoh_intake * 0.4 / self.mtd_weight
  
  class Meta:
    db_table = 'mtd_monkeys_to_drinking_experiments'


class RequestStatus(models.Model):
  rqs_status_id = models.AutoField('ID', primary_key=True)
  rqs_status_name = models.CharField('Name', max_length=100, unique=True, null=False,
                                     help_text='The name of the status.')
  rqs_status_description = models.TextField('Description', null=True,
                                            help_text='The description of the status.')
  
  def __unicode__(self):
    return self.rqs_status_name
  
  class Meta:
    db_table = 'rqs_request_statuses'


class FixType(models.Model):
  fxt_fix_id = models.AutoField('ID', primary_key=True)
  fxt_fix_name = models.CharField('Name', max_length=100, unique=True, null=False,
                                  help_text='The name of the fix type.')
  fxt_fix_description = models.TextField('Description', null=True,
                                         help_text='The description of this fix type.')
  
  def __unicode__(self):
    return self.fxt_fix_name
  
  class Meta:
    db_table = 'fxt_fix_types'


class TissueType(models.Model):
  tst_type_id = models.AutoField('ID', primary_key=True)
  tst_tissue_name = models.CharField('Name', max_length=100, unique=True, null=False,
                                     help_text='The name of the tissue type.')
  tst_description = models.TextField('Description', null=True,
                                     help_text='The description of the tissue type.')
  fixes = models.ManyToManyField(FixType, through='FixToTissueType',
                                 verbose_name='Available Fixes',
                                 help_text='The fix types available for this tissue type.')
  
  def __unicode__(self):
    return self.tst_tissue_name

  def get_id(self):
    return self.tst_type_id

  def get_name(self):
    return self.tst_tissue_name
  
  class Meta:
    db_table = 'tst_tissue_types'


class FixToTissueType(models.Model):
  ftt_fix_to_tissue_type_id = models.AutoField('ID', primary_key=True)
  FixType = models.ForeignKey(FixType, null=False, related_name='+', db_column='fxt_fix_id',
                              verbose_name='Fix Type',)
  TissueType = models.ForeignKey(TissueType, null=False, related_name='+', db_column='tst_type_id',
                                 verbose_name='Tissue Type')
  
  def __unicode__(self):
    return self.TissueType.tst_tissue_name + ' - ' + self.FixType.fxt_fix_name
  
  class Meta:
    db_table = 'ftt_fix_to_tissue_types'
    unique_together=('FixType', 'TissueType')


class Unit(models.Model):
  unt_unit_id = models.AutoField('ID', primary_key=True)
  unt_unit_name = models.CharField('Name', max_length=100, unique=True, null=False,
                                   help_text='The name of the unit type. (ex. ml, mg)')
  
  def __unicode__(self):
    return self.unt_unit_name
  
  class Meta:
    db_table = 'unt_units'


class Request(models.Model, DiffingMixin):
  REFERRAL_CHOICES = (
    ('Internet Search','Internet Search'),
    ('Publication', 'Publication'),
    ('Professional Meeting', 'Professional Meeting'),
    ('MATRR Staff/Investigator', 'MATRR Staff/Investigator'),
    ('Colleague', 'Colleague'),
    ('other', 'other'),
  )
  req_request_id = models.AutoField('ID', primary_key=True)
  request_status = models.ForeignKey(RequestStatus, null=False, db_column='rqs_status_id',)
  cohort = models.ForeignKey(Cohort, null=False, db_column='coh_cohort_id', editable=False,)
  user = models.ForeignKey(User, null=False, db_column='usr_user_id', editable=False,)
  req_modified_date = models.DateTimeField( auto_now_add=True, editable=False, auto_now=True)
  req_request_date = models.DateTimeField( editable=False, auto_now_add=True)
  req_experimental_plan = models.FileField('Experimental Plan', upload_to='experimental_plans/',
                                           default='', null=True, blank=True,
                                           help_text='You may upload a detailed description of your research plans for the tissues you are requesting.')
  req_project_title = models.CharField('Project Title', null=False, blank=False,
                                       max_length=200,
                                       help_text='The name of the project or proposal these tissues will be used in.')
  req_reason = models.TextField('Reason for Tissue Request', null=False, blank=False,
                                help_text='Please provide a short paragraph describing the hypothesis and methods proposed.')
  req_progress_agreement = models.BooleanField('Would you be willing to supply us with a progress report on the results obtained from our tissue? (We will request an update 90 after the tissues are shipped.)',
                                               null=False,)
  req_referred_by = models.CharField('How did you hear about the tissue bank?',
                                     choices=REFERRAL_CHOICES,
                                     null=False,
                                     max_length=100)
  req_notes = models.TextField('Notes', null=True, blank=True)
  
  def __unicode__(self):
    return 'User: ' + self.user.username + \
           ' Cohort: ' + self.cohort.coh_cohort_name + \
           ' Date: ' + self.req_request_date.strftime("%I:%M%p  %m/%d/%y")

  def get_requested_tissue_count(self):
    return self.tissue_request_set.count() + \
           self.brain_region_request_set.count() + \
           self.blood_and_genetic_request_set.count()
  
  class Meta:
    db_table = 'req_requests'
  
  def save(self, force_insert=False, force_update=False, using=None):
    if self.request_status.rqs_status_id != self._original_state['request_status_id']\
        and self._original_state['request_status_id'] == RequestStatus.objects.get(rqs_status_name='Cart').rqs_status_id:
      self.req_request_date = datetime.now()
    self.req_modified_date = datetime.now()
    self._previous_status_id = self._original_state['request_status_id']
    super(Request, self).save(force_insert, force_update, using)


class RequestRevision(models.Model):
  rqv_request_revision_id = models.AutoField(primary_key=True)
  req_request = models.ForeignKey(Request, null=False, related_name='request_revision_set', db_column='req_request_id', editable=False)
  rqv_version_number = models.IntegerField(null=False, editable=False)
  rqv_request_date = models.DateTimeField(null=False, editable=False)
  rqv_experimental_plan = models.FileField(upload_to='experimental_plans/', editable=False)
  rqv_notes = models.TextField(null=True, editable=False)
  
  def __unicode__(self):
    return 'Request: ' + self.req_request.req_request_id + ' Revision: ' + self.rqv_version_number
  
  class Meta:
    db_table = 'rqv_request_revisions'
    unique_together = ('req_request', 'rqv_version_number')


class TissueRequest(models.Model):
  rtt_tissue_request_id = models.AutoField(primary_key=True)
  req_request = models.ForeignKey(Request, null=False, related_name='tissue_request_set', db_column='req_request_id')
  tissue_type = models.ForeignKey(TissueType, null=False, related_name='tissue_request_set', db_column='tst_type_id')
  fix_type = models.ForeignKey(FixType, null=False, related_name='tissue_request_set', db_column='fxt_fix_id', verbose_name='Fix',
      help_text='Please select the appropriate fix type.')
  rtt_amount = models.FloatField('Amount',
      help_text='Please enter the amount of tissue you need.')
  unit = models.ForeignKey(Unit, null = False, related_name='+', db_column='unt_unit_id', 
      help_text='Please select the unit of measure.')
  rtt_notes = models.TextField('Notes', null=True, blank=True,
      help_text='Use this field to add any requirements that are not covered by the above form. You may also enter any comments you have on this particular tissue request.')
  monkeys = models.ManyToManyField(Monkey, db_table='mtr_monkeys_to_tissue_requests',
                                 verbose_name='Requested Monkeys',
                                 help_text='The monkeys this tissue is requested from.')
  
  def __unicode__(self):
    return self.tissue_type.tst_tissue_name + ': ' + self.fix_type.fxt_fix_name

  def get_tissue(self):
    return self.tissue_type

  def get_id(self):
    return self.rtt_tissue_request_id
  
  def has_notes(self):
    return self.rtt_notes is not None and self.rtt_notes != ''

  def get_notes(self):
    return self.rtt_notes

  def get_data(self):
    return [['Tissue Type', self.tissue_type],
            ['Fix', self.fix_type],
            ['Amount', str(self.rtt_amount) + self.unit.unt_unit_name]]

  def get_type_url(self):
    return 'peripherals'

  def get_reviews(self):
    return self.tissue_request_review_set.all()

  class Meta:
    db_table = 'rtt_requests_to_tissue_types'
    unique_together = (('req_request', 'tissue_type', 'fix_type'),)


class TissueRequestRevision(models.Model):
  rtv_tissue_request_id = models.AutoField(primary_key=True)
  request_revision = models.ForeignKey(RequestRevision, null=False, related_name='tissue_request_revision_set', db_column='rqv_request_revision_id', editable=False)
  tissue_type = models.ForeignKey(TissueType, null=False, related_name='tissue_request_revision_set', db_column='tst_type_id', editable=False)
  fix_type = models.ForeignKey(FixType, null=False, related_name='tissue_request_revision_set', db_column='fxt_fix_id', editable=False, verbose_name='Fix',)
  rtv_amount = models.FloatField('Amount', editable=False)
  unit = models.ForeignKey(Unit, null = False, related_name='+', db_column='unt_unit_id', editable=False, verbose_name='Unit',)
  rtv_notes = models.TextField('Notes', null=True, editable=False,)
  monkeys = models.ManyToManyField(Monkey, db_table='mtv_monkeys_to_tissue_request_revisions',
                                 verbose_name='Requested Monkeys',
                                 help_text='The monkeys this tissue is requested from.',
                                 editable=False)
  
  def __unicode__(self):
    return 'Request Revision: ' + self.request_revision.rqv_request_revision_id + \
           ' Tissue: ' + self.tissue_type.tst_tissue_name
  
  class Meta:
    db_table = 'rtv_request_to_tissue_type_revisions'


class BrainBlock(models.Model):
  bbl_block_id = models.AutoField(primary_key=True)
  bbl_block_name = models.CharField('Name', max_length=100, unique=True, null=False,
                                     help_text='The name of the brain block.')
  bbl_description = models.TextField('Description', null=True, blank=True,
                                     help_text='The description of the brain block.')
  
  def __unicode__(self):
    return self.bbl_block_name

  def get_id(self):
    return self.bbl_block_id

  def get_name(self):
    return self.bbl_block_name
  
  class Meta:
    db_table = 'bbl_brain_blocks'


class BrainRegion(models.Model):
  bre_region_id = models.AutoField(primary_key=True)
  bre_region_name = models.CharField('Name', max_length=100, unique=True, null=False,
                                     help_text='The name of the brain region.')
  bre_description = models.TextField('Description', null=True, blank=True,
                               help_text='Please enter a detailed description of the brain region here.')
  
  def __unicode__(self):
    return self.bre_region_name

  def get_id(self):
    return self.bre_region_id

  def get_name(self):
    return self.bre_region_name
  
  class Meta:
    db_table = 'bre_brain_regions'


class BrainRegionRequest(models.Model):
  rbr_region_request_id = models.AutoField(primary_key=True)
  req_request = models.ForeignKey(Request, null=False, related_name='brain_region_request_set', db_column='req_request_id')
  brain_region = models.ForeignKey(BrainRegion, null=False, related_name='brain_region_request_set', db_column='bre_region_id')
  rbr_notes = models.TextField('Notes', null=True, blank=True,
                               help_text='Use this field to add any requirements that are not covered by the above form. You may also enter any comments you have on this particular request.')
  monkeys = models.ManyToManyField(Monkey, db_table='mbr_monkeys_to_brain_region_requests',
                                 verbose_name='Requested Monkeys',
                                 help_text='The monkeys this region is requested from.')
  
  def __unicode__(self):
    return str(self.brain_region)

  def get_tissue(self):
    return self.brain_region

  def get_id(self):
    return self.rbr_region_request_id

  def has_notes(self):
    return self.rbr_notes != None and self.rbr_notes != ''

  def get_notes(self):
    return self.rbr_notes

  def get_data(self):
    return [['Brain Region', self.brain_region],]

  def get_type_url(self):
    return 'regions'

  def get_reviews(self):
    return self.brain_region_request_review_set.all()

  class Meta:
    db_table = 'rbr_requests_to_brain_regions'
    unique_together = ('req_request', 'brain_region')


class BrainRegionRequestRevision(models.Model):
  rbv_revision_id = models.AutoField(primary_key=True)
  request_revision = models.ForeignKey(RequestRevision, null=False, related_name='brain_region_request_revision_set', db_column='rqv_request_revision_id', editable=False)
  brain_region = models.ForeignKey(BrainRegion, null=False, related_name='brain_region_request_revision_set', db_column='bbl_block_id', editable=False)
  brv_notes = models.TextField(null=True, blank=True, editable=False)
  monkeys = models.ManyToManyField(Monkey, db_table='mrv_monkeys_to_brain_region_request_revisions',
                                 verbose_name='Requested Monkeys',
                                 help_text='The monkeys this block is requested from.')
  
  def __unicode__(self):
    return self.request_revision + ': ' + self.brain_region
  
  class Meta:
    db_table = 'rbv_requests_to_brain_regions_revisions'
    unique_together = ('request_revision', 'brain_region')


############################################################################
# The microdissected region code is commented out because (at least for
# upcoming requests) it is no longer needed.
# There may be a use for this when we implement archived tissues, so
# commenting the code out is better than deleting it for now.
############################################################################
#class MicrodissectedRegion(models.Model):
#  bmr_microdissected_id = models.AutoField(primary_key=True)
#  bmr_microdissected_name = models.CharField('Name', max_length=100, unique=True, null=False,
#                                     help_text='The name of the microdissected brain region.')
#  bmr_description = models.TextField('Notes', null=True, blank=True,
#                               help_text='Use this field to add any requirements that are not covered by the above form. You may also enter any comments you have on this particular request.')
#
#  def __unicode__(self):
#    return self.bmr_microdissected_name
#
#  def get_id(self):
#    return self.bmr_microdissected_id
#
#  def get_name(self):
#    return self.bmr_microdissected_name
#
#  class Meta:
#    db_table = 'bmr_brain_microdissected_regions'
#
#
#class MicrodissectedRegionRequest(models.Model):
#  rmr_microdissected_request_id = models.AutoField(primary_key=True)
#  req_request = models.ForeignKey(Request, null=False, related_name='microdissected_region_request_set', db_column='req_request_id')
#  microdissected_region = models.ForeignKey(MicrodissectedRegion, null=False, related_name='microdissected_region_request_set', db_column='bmr_microdissected_id')
#  rmr_notes = models.TextField('Notes', null=True, blank=True,
#                               help_text='Use this field to add any requirements that are not covered by the above form. You may also enter any comments you have on this particular request.')
#  monkeys = models.ManyToManyField(Monkey, db_table='mmr_monkeys_to_microdissected_region_requests',
#                                 verbose_name='Requested Monkeys',
#                                 help_text='The monkeys this region is requested from.')
#
#  def __unicode__(self):
#    return str(self.microdissected_region)
#
#  def get_tissue(self):
#    return self.microdissected_region
#
#  def get_id(self):
#    return self.rmr_microdissected_request_id
#
#  def get_id(self):
#    return rmr_microdissected_request_id
#
#  def has_notes(self):
#    return self.rmr_notes != None and self.rmr_notes != ''
#
#  def get_notes(self):
#    return self.rmr_notes
#
#  def get_data(self):
#    return [['Microdissected Region', self.microdissected_region],]
#
#  def get_type_url(self):
#    return 'microdissected'
#
#  def get_reviews(self):
#    return self.microdissected_region_request_review_set.all()
#
#  class Meta:
#    db_table = 'rmr_requests_to_microdissected_regions'
#    unique_together = ('req_request', 'microdissected_region')
#
#
#class MicrodissectedRegionRequestRevision(models.Model):
#  mrv_id = models.AutoField(primary_key=True)
#  request_revision = models.ForeignKey(RequestRevision, null=False, related_name='microdissected_region_request_revision_set', db_column='rqv_request_revision_id', editable=False)
#  microdissected_region = models.ForeignKey(MicrodissectedRegion, null=False, related_name='microdissected_region_request_revision_set', db_column='bmr_microdissected_id', editable=False)
#  mrv_notes = models.TextField(null=True, blank=True, editable=False)
#  monkeys = models.ManyToManyField(Monkey, db_table='mmv_monkeys_to_microdissected_region_request_revisions',
#                                 verbose_name='Requested Monkeys',
#                                 help_text='The monkeys this region is requested from.')
#
#  def __unicode__(self):
#    return self.request_revision + ': ' + self.microdissected_region
#
#  class Meta:
#    db_table = 'mrv_requests_to_microdissected_regions_revisions'
#    unique_together = ('request_revision', 'microdissected_region')


class BloodAndGenetic(models.Model):
  bag_id = models.AutoField(primary_key=True)
  bag_name = models.CharField('Name', max_length=100, unique=True, null=False,
                                     help_text='The name of the blood or genetics sample.')
  bag_description = models.TextField('Notes', null=True, blank=True,
                               help_text='Use this field to add any requirements that are not covered by the above form. You may also enter any comments you have on this particular request.')
  
  def __unicode__(self):
    return self.bag_name

  def get_id(self):
    return self.bag_id

  def get_name(self):
    return self.bag_name
  
  class Meta:
    db_table = 'bag_blood_and_genetics'


class BloodAndGeneticRequest(models.Model):
  rbg_id = models.AutoField(primary_key=True)
  req_request = models.ForeignKey(Request, null=False, related_name='blood_and_genetic_request_set', db_column='req_request_id')
  blood_genetic_item = models.ForeignKey(BloodAndGenetic, null=False, related_name='blood_and_genetic_request_set', db_column='bag_id')
  rbg_notes = models.TextField('Notes', null=True, blank=True,
                               help_text='Use this field to add any requirements that are not covered by the above form. You may also enter any comments you have on this particular request.')
  monkeys = models.ManyToManyField(Monkey, db_table='mgr_monkeys_to_blood_and_genetic_requests',
                                 verbose_name='Requested Monkeys',
                                 help_text='The monkeys this region is requested from.')
  
  def __unicode__(self):
    return str(self.blood_genetic_item)

  def get_tissue(self):
    return self.blood_genetic_item

  def get_id(self):
    return self.rbg_id

  def has_notes(self):
    return self.rbg_notes != None and self.rbrg_notes != ''

  def get_notes(self):
    return self.rbg_notes

  def get_data(self):
    return [['Blood/Genetic Sample', self.blood_genetic_item],]

  def get_type_url(self):
    return 'samples'

  def get_reviews(self):
    return self.blood_and_genetic_request_review_set.all()
  
  class Meta:
    db_table = 'rbg_requests_to_blood_and_genetics'
    unique_together = ('req_request', 'blood_genetic_item')


class BloodAndGeneticRequestRevision(models.Model):
  brr = models.AutoField(primary_key=True)
  request_revision = models.ForeignKey(RequestRevision, null=False, related_name='blood_and_genetic_request_revision_set', db_column='rqv_request_revision_id', editable=False)
  blood_genetic_item = models.ForeignKey(BloodAndGenetic, null=False, related_name='blood_and_genetic_request_revision_set', db_column='bag_id', editable=False)
  brr_notes = models.TextField(null=True, blank=True, editable=False)
  monkeys = models.ManyToManyField(Monkey, db_table='mgv_monkeys_to_blood_genetic_request_revisions',
                                 verbose_name='Requested Monkeys',
                                 help_text='The monkeys this region is requested from.')
  
  def __unicode__(self):
    return self.request_revision + ': ' + self.blood_genetic_item
  
  class Meta:
    db_table = 'grr_requests_to_blood_and_genetic_revisions'
    unique_together = ('request_revision', 'blood_genetic_item')


class CustomTissueRequest(models.Model):
  '''
  This class is for custom tissue requests.
  It differs from the other request classes by
  not having a reference to a tissue class.
  '''
  ctr_id = models.AutoField(primary_key=True)
  req_request = models.ForeignKey(Request, null=False, related_name='custom_tissue_request_set', db_column='req_request_id')
  ctr_description = models.TextField('Detailed Description',
                                     null=False,
                                     blank=False,
                                     help_text='Please enter a detailed description of the tissue you need.  List any special requirements here.')
  ctr_amount = models.CharField('Amount', null=False, blank=False,
                                max_length=100,
                                help_text='Please enter the amount of tissue that you need.')
  monkeys = models.ManyToManyField(Monkey, db_table='mcr_monkeys_to_custom_tissue_requests',
                                 verbose_name='Requested Monkeys',
                                 help_text='The monkeys this tissue is requested from.')

  def __unicode__(self):
    return str('Custom Tissue Request')

  def get_tissue(self):
    raise NotImplementedError()

  def get_id(self):
    return self.ctr_id

  def has_notes(self):
    return False

  def get_notes(self):
    return None

  def get_data(self):
    return [['Custom Tissue Request', self.ctr_description],
            ['Amount', self.ctr_amount]]

  def get_type_url(self):
    raise NotImplementedError()

  def get_reviews(self):
    return self.custom_tissue_request_review_set.all()

  class Meta:
    db_table = 'ctr_custom_tissue_requests'


class Event(models.Model):
  id = models.AutoField('ID', primary_key=True)
  name = models.CharField('Name', max_length=100, unique=True, null=False,
                          help_text='The name of the event.')
  description = models.TextField('Description', null=True, blank=True,
                                 help_text='A description of the event.')
  date = models.DateField('Date',
                          help_text='The date of the event.')

  def __unicode__(self):
    return self.name + ' (' + str(self.date) + ')'


class Review(models.Model):
  rvs_review_id = models.AutoField(primary_key=True)
  req_request = models.ForeignKey(Request, null=False, db_column='req_request_id', editable=False)
  user = models.ForeignKey(User, null=False, db_column='usr_user_id', editable=False)
  rvs_notes = models.TextField(null=True, blank=True, verbose_name='Notes')
  
  def __unicode__(self):
    return 'Review of request: <' + str(self.req_request) + '> by: ' + str(self.user)
  
  def is_finished(self):
    return all( tissue_request.is_finished() for tissue_request in TissueRequestReview.objects.filter(review=self.rvs_review_id)) \
    and all( region_request.is_finished() for region_request in BrainRegionRequestReview.objects.filter(review=self.rvs_review_id) ) \
    and all( sample_request.is_finished() for sample_request in BloodAndGeneticRequestReview.objects.filter(review=self.rvs_review_id) )
  
  class Meta:
    db_table = 'rvs_reviews'
    unique_together = ('user', 'req_request')


class ReviewRevision(models.Model):
  rvr_revision_id = models.AutoField(primary_key=True)
  review = models.ForeignKey(Review, null=False, related_name='review_revision_set', db_column='rvs_review_id', editable=False)
  request_revision = models.ForeignKey(RequestRevision, null=False, related_name='review_revision_set', db_column='rqv_request_revision_id', editable=False)
  rvr_notes = models.TextField(null=True, verbose_name='Notes')
  
  def __unicode__(self):
    return str(self.review) + ' ' + str(self.request_revision)
  
  class Meta:
    db_table = 'rvr_review_revisions'
    unique_together = ('review', 'request_revision')


class TissueRequestReview(models.Model):
  vtr_request_review_id = models.AutoField(primary_key=True)
  review = models.ForeignKey(Review, null=False, related_name='tissue_request_review_set', db_column='rvs_review_id', editable=False)
  tissue_request = models.ForeignKey(TissueRequest, null=False, related_name='tissue_request_review_set', db_column='rtt_tissue_request_id', editable=False)
  vtr_scientific_merit = models.PositiveSmallIntegerField('Scientific Merit', null=True, blank=False, 
      help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
  vtr_quantity = models.PositiveSmallIntegerField('Quantity', null=True, blank=False, 
      help_text='Enter a number between 0 and 10, with 0 being the too little, 10 being too much, and 5 being an appropriate amount.')
  vtr_priority = models.PositiveSmallIntegerField('Priority', null=True, blank=False,
      help_text='Enter a number between 0 and 10, with 0 being the lowest priority and 10 being the highest.')
  vtr_notes = models.TextField(null=True, blank=True, verbose_name='Notes')
  
  def __unicode__(self):
    return 'Review: ' + str(self.review) + ' TissueRequest: ' + str(self.tissue_request)
  
  def is_finished(self):
    return self.vtr_scientific_merit is not None and \
        self.vtr_quantity is not None and \
        self.vtr_priority is not None

  def get_request(self):
    return self.tissue_request

  def get_merit(self):
    return self.vtr_scientific_merit

  def get_quantity(self):
    return self.vtr_quantity

  def get_priority(self):
    return self.vtr_priority

  def has_notes(self):
    return self.vtr_notes != None and self.vtr_notes != ''

  def get_notes(self):
    return self.vtr_notes

  class Meta:
    db_table = 'vtr_reviews_to_tissue_requests'
    unique_together = ('review', 'tissue_request')


class TissueRequestReviewRevision(models.Model):
  vtv_review_revision_id = models.AutoField(primary_key=True)
  review_revision = models.ForeignKey(ReviewRevision, null=False, related_name='tissue_request_review_revision_set', db_column='rvr_revision_id', editable=False)
  tissue_request_revision = models.ForeignKey(TissueRequestRevision, null=False, related_name='tissue_request_review_revision_set', db_column='rtv_tissue_request_id', editable=False)
  vtv_scientific_merit = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Scientific Merit', 
      help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
  vtv_quantity = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Quantity', 
      help_text='Enter a number between 0 and 10, with 0 being the too little, 10 being too much, and 5 being an appropriate amount.')
  vtv_priority = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Priority',
      help_text='Enter a number between 0 and 10, with 0 being the lowest priority and 10 being the highest.')
  vtv_notes = models.TextField(null=True, blank=True, verbose_name='Notes')
  
  def __unicode__(self):
    return 'ReviewRevision: ' + self.review_revision + ' TissueRequestRevision: ' + self.tissue_request_revision
    
  class Meta:
    db_table = 'vtv_reviews_to_tissue_request_revisions'
    unique_together = ('review_revision', 'tissue_request_revision')


class BrainRegionRequestReview(models.Model):
  vbr_region_request_review_id = models.AutoField(primary_key=True)
  review = models.ForeignKey(Review, null=False, related_name='brain_region_request_review_set', db_column='rvs_review_id', editable=False)
  brain_region_request = models.ForeignKey(BrainRegionRequest, null=False, related_name='brain_region_request_review_set', db_column='rbr_region_request_id', editable=False)
  vbr_scientific_merit = models.PositiveSmallIntegerField('Scientific Merit', null=True, blank=False, 
      help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
  vbr_quantity = models.PositiveSmallIntegerField('Quantity', null=True, blank=False, 
      help_text='Enter a number between 0 and 10, with 0 being the too little, 10 being too much, and 5 being an appropriate amount.')
  vbr_priority = models.PositiveSmallIntegerField('Priority', null=True, blank=False,
      help_text='Enter a number between 0 and 10, with 0 being the lowest priority and 10 being the highest.')
  vbr_notes = models.TextField('Notes', null=True, blank=True,)
  
  def __unicode__(self):
    return 'Review: ' + str(self.review) + ' BrainRegionRequest: ' + str(self.brain_region_request)
  
  def is_finished(self):
    return self.vbr_scientific_merit is not None and \
        self.vbr_quantity is not None and \
        self.vbr_priority is not None

  def get_request(self):
    return self.brain_region_request

  def get_merit(self):
    return self.vbr_scientific_merit

  def get_quantity(self):
    return self.vbr_quantity

  def get_priority(self):
    return self.vbr_priority

  def has_notes(self):
    return self.vbr_notes != None and self.vbr_notes != ''

  def get_notes(self):
    return self.vbr_notes

  class Meta:
    db_table = 'vbr_reviews_to_brain_region_requests'
    unique_together = ('review', 'brain_region_request')


class BrainRegionRequestReviewRevision(models.Model):
  vrv_review_revision_id = models.AutoField(primary_key=True)
  review_revision = models.ForeignKey(ReviewRevision, null=False, related_name='brain_region_request_review_revision_set', db_column='rvr_revision_id', editable=False)
  brain_region_request_revision = models.ForeignKey(BrainRegionRequestRevision, null=False, related_name='brain_region_request_review_revision_set', db_column='rbv_revision_id', editable=False)
  vrv_scientific_merit = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Scientific Merit', 
      help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
  vrv_quantity = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Quantity', 
      help_text='Enter a number between 0 and 10, with 0 being the too little, 10 being too much, and 5 being an appropriate amount.')
  vrv_priority = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Priority',
      help_text='Enter a number between 0 and 10, with 0 being the lowest priority and 10 being the highest.')
  vrv_notes = models.TextField(null=True, blank=True, verbose_name='Notes')
  
  def __unicode__(self):
    return 'ReviewRevision: ' + self.review_revision + ' BrainRegionRequestRevision: ' + self.brain_region_request_revision
    
  class Meta:
    db_table = 'vrv_reviews_to_brain_region_request_revisions'
    unique_together = ('review_revision', 'brain_region_request_revision')


############################################################################
# The microdissected region code is commented out because (at least for
# upcoming requests) it is no longer needed.
# There may be a use for this when we implement archived tissues, so
# commenting the code out is better than deleting it for now.
############################################################################
#class MicrodissectedRegionRequestReview(models.Model):
#  vmr_microdissected_request_review_id = models.AutoField(primary_key=True)
#  review = models.ForeignKey(Review, null=False, related_name='microdissected_region_request_review_set', db_column='rvs_review_id', editable=False)
#  microdissected_region_request = models.ForeignKey(MicrodissectedRegionRequest, null=False,
#                                                    related_name='microdissected_region_request_review_set',
#                                                    db_column='rmr_block_request_id',
#                                                    editable=False)
#  vmr_scientific_merit = models.PositiveSmallIntegerField('Scientific Merit', null=True, blank=False,
#      help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
#  vmr_quantity = models.PositiveSmallIntegerField('Quantity', null=True, blank=False,
#      help_text='Enter a number between 0 and 10, with 0 being the too little, 10 being too much, and 5 being an appropriate amount.')
#  vmr_priority = models.PositiveSmallIntegerField('Priority', null=True, blank=False,
#      help_text='Enter a number between 0 and 10, with 0 being the lowest priority and 10 being the highest.')
#  vmr_notes = models.TextField('Notes', null=True, blank=True,)
#
#  def __unicode__(self):
#    return 'Review: ' + str(self.review) + ' MicrodissectedRegionRequest: ' + str(self.microdissected_region_request)
#
#  def is_finished(self):
#    return self.vmr_scientific_merit is not None and \
#        self.vmr_quantity is not None and \
#        self.vmr_priority is not None
#
#  def get_request(self):
#    return self.microdissected_region_request
#
#  def get_merit(self):
#    return self.vmr_scientific_merit
#
#  def get_quantity(self):
#    return self.vmr_quantity
#
#  def get_priority(self):
#    return self.vmr_priority
#
#  def has_notes(self):
#    return self.vmr_notes != None and self.vmr_notes != ''
#
#  def get_notes(self):
#    return self.vmr_notes
#
#  class Meta:
#    db_table = 'vmr_reviews_to_microdissected_region_requests'
#    unique_together = ('review', 'microdissected_region_request')
#
#
#class MicrodissectedRegionRequestReviewRevision(models.Model):
#  vmv_review_revision_id = models.AutoField(primary_key=True)
#  review_revision = models.ForeignKey(ReviewRevision, null=False, related_name='microdissected_region_request_review_revision_set', db_column='rvr_revision_id', editable=False)
#  microdissected_region_request_revision = models.ForeignKey(MicrodissectedRegionRequestRevision, null=False, related_name='microdissected_region_request_review_revision_set', db_column='mrv_id', editable=False)
#  vmv_scientific_merit = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Scientific Merit',
#      help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
#  vmv_quantity = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Quantity',
#      help_text='Enter a number between 0 and 10, with 0 being the too little, 10 being too much, and 5 being an appropriate amount.')
#  vmv_priority = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Priority',
#      help_text='Enter a number between 0 and 10, with 0 being the lowest priority and 10 being the highest.')
#  vmv_notes = models.TextField(null=True, blank=True, verbose_name='Notes')
#
#  def __unicode__(self):
#    return 'ReviewRevision: ' + self.review_revision + ' MicrodissectedRegionRequestRevision: ' + self.microdissected_region_request_revision
#
#  class Meta:
#    db_table = 'vmv_reviews_to_microdissected_region_request_revisions'
#    unique_together = ('review_revision', 'microdissected_region_request_revision')


class BloodAndGeneticRequestReview(models.Model):
  vbg_blood_genetic_request_review_id = models.AutoField(primary_key=True)
  review = models.ForeignKey(Review, null=False, related_name='blood_and_genetic_request_review_set', db_column='rvs_review_id', editable=False)
  blood_and_genetic_request = models.ForeignKey(BloodAndGeneticRequest, null=False, related_name='blood_and_genetic_request_review_set', db_column='rbg_id', editable=False)
  vbg_scientific_merit = models.PositiveSmallIntegerField('Scientific Merit', null=True, blank=False, 
      help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
  vbg_quantity = models.PositiveSmallIntegerField('Quantity', null=True, blank=False, 
      help_text='Enter a number between 0 and 10, with 0 being the too little, 10 being too much, and 5 being an appropriate amount.')
  vbg_priority = models.PositiveSmallIntegerField('Priority', null=True, blank=False,
      help_text='Enter a number between 0 and 10, with 0 being the lowest priority and 10 being the highest.')
  vbg_notes = models.TextField('Notes', null=True, blank=True,)
  
  def __unicode__(self):
    return 'Review: ' + str(self.review) + ' BloodAndGeneticRequest: ' + str(self.blood_and_genetic_request)
  
  def is_finished(self):
    return self.vbg_scientific_merit is not None and \
        self.vbg_quantity is not None and \
        self.vbg_priority is not None

  def get_request(self):
    return self.blood_and_genetic_request

  def get_merit(self):
    return self.vbg_scientific_merit

  def get_quantity(self):
    return self.vbg_quantity

  def get_priority(self):
    return self.vbg_priority

  def has_notes(self):
    return self.vbg_notes != None and self.vbg_notes != ''

  def get_notes(self):
    return self.vbg_notes
  
  class Meta:
    db_table = 'vbg_reviews_to_blood_and_genetic_requests'
    unique_together = ('review', 'blood_and_genetic_request')


class BloodAndGeneticRequestReviewRevision(models.Model):
  vgv_review_revision_id = models.AutoField(primary_key=True)
  review_revision = models.ForeignKey(ReviewRevision, null=False, related_name='blood_genetic_request_review_revision_set', db_column='rvr_revision_id', editable=False)
  blood_and_genetic_request_revision = models.ForeignKey(BloodAndGeneticRequestRevision, null=False, related_name='blood_genetic_request_review_revision_set', db_column='mrv_id', editable=False)
  vgv_scientific_merit = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Scientific Merit', 
      help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
  vgv_quantity = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Quantity', 
      help_text='Enter a number between 0 and 10, with 0 being the too little, 10 being too much, and 5 being an appropriate amount.')
  vgv_priority = models.PositiveSmallIntegerField(null=True, blank=False, verbose_name='Priority',
      help_text='Enter a number between 0 and 10, with 0 being the lowest priority and 10 being the highest.')
  vgv_notes = models.TextField(null=True, blank=True, verbose_name='Notes')
  
  def __unicode__(self):
    return 'ReviewRevision: ' + self.review_revision + ' BloodAndGeneticRequestRevision: ' + self.blood_and_genetic_request_revision
    
  class Meta:
    db_table = 'vgv_reviews_to_blood_and_genetic_request_revisions'
    unique_together = ('review_revision', 'blood_and_genetic_request_revision')


class CustomTissueRequestReview(models.Model):
  vct_review_id = models.AutoField(primary_key=True)
  review = models.ForeignKey(Review, null=False, related_name='custom_tissue_request_review_set', db_column='rvs_review_id', editable=False)
  custom_tissue_request = models.ForeignKey(CustomTissueRequest,
                                            null=False,
                                            related_name='custom_tissue_request_review_set',
                                            db_column='rbg_id',
                                            editable=False)
  vct_scientific_merit = models.PositiveSmallIntegerField('Scientific Merit', null=True, blank=False,
      help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
  vct_quantity = models.PositiveSmallIntegerField('Quantity', null=True, blank=False,
      help_text='Enter a number between 0 and 10, with 0 being the too little, 10 being too much, and 5 being an appropriate amount.')
  vct_priority = models.PositiveSmallIntegerField('Priority', null=True, blank=False,
      help_text='Enter a number between 0 and 10, with 0 being the lowest priority and 10 being the highest.')
  vct_notes = models.TextField('Notes', null=True, blank=True,)

  def __unicode__(self):
    return 'Review: ' + str(self.review) + ' BloodAndGeneticRequest: ' + str(self.blood_and_genetic_request)

  def is_finished(self):
    return self.vct_scientific_merit is not None and \
        self.vct_quantity is not None and \
        self.vct_priority is not None

  def get_request(self):
    return self.custom_tissue_request

  def get_merit(self):
    return self.vct_scientific_merit

  def get_quantity(self):
    return self.vct_quantity

  def get_priority(self):
    return self.vct_priority

  def has_notes(self):
    return self.vct_notes != None and self.vct_notes != ''

  def get_notes(self):
    return self.vct_notes

  class Meta:
    db_table = 'vct_reviews_to_custom_tissue_requests'
    unique_together = ('review', 'custom_tissue_request')


# put any signal callbacks down here after the model declarations

# this is a method that should be called after a request is saved.
# It will check to see if there was a status change and, if so, 
# it should take the appropriate action.
#
# For example, if the status changes from 'cart' to 'submitted', 
# new reviews for each member of the committee group should be created.
@receiver(post_save, sender=Request)
def request_post_save(**kwargs):
  # get the Request instance
  req_request = kwargs['instance']
  # check if there was a change in the status 
  if req_request._previous_status_id is None or \
      req_request.request_status_id == req_request._previous_status_id:
    # if there was no change, no work needs to be done
    return
  
  current_status = RequestStatus.objects.get(rqs_status_id=req_request.request_status_id)
  previous_status = RequestStatus.objects.get(rqs_status_id=req_request._previous_status_id)
  
  # now check to see what the current status is and take the appropriate action
  if current_status == RequestStatus.objects.get(rqs_status_name='Submitted')\
      and previous_status == RequestStatus.objects.get(rqs_status_name='Cart'):
    # the status was changed from Cart to Submitted, so create new reviews
    
    # start by finding all members of the group 'Committee'
    committee_group = Group.objects.get(name='Committee')
    committee_members = committee_group.user_set.all()
    # get all the tissue requests for the request
    brain_region_requests = BrainRegionRequest.objects.filter(req_request=req_request.req_request_id)
    #microdissected_requests = MicrodissectedRegionRequest.objects.filter(req_request=req_request.req_request_id)
    peripheral_tissue_requests = TissueRequest.objects.filter(req_request=req_request.req_request_id)
    sample_requests = BloodAndGeneticRequest.objects.filter(req_request=req_request.req_request_id)

    # for each committee member, create a new review for the request
    for user in committee_members:
      review = Review(req_request=req_request, user=user)
      review.save()
      # create a new TissueRequestReview for each TissueRequest
      for tissue_request in brain_region_requests:
        BrainRegionRequestReview(review=review, brain_region_request=tissue_request).save()
#      for tissue_request in microdissected_requests:
#        MicrodissectedRegionRequestReview(review=review, microdissected_region_request=tissue_request).save()
      for tissue_request in peripheral_tissue_requests:
        TissueRequestReview(review=review, tissue_request=tissue_request).save()
      for tissue_request in sample_requests:
        BloodAndGeneticRequestReview(review=review, blood_and_genetic_request=tissue_request).save()
  
  req_request._previous_status_id = None


# This is a method to check to see if a user_id exists that does not have
# an account attached to it.
@receiver(post_save, sender=User)
def user_post_save(**kwargs):
  #check to see if user exists in accounts relation
  user = kwargs['instance']
  if not Account.objects.filter(user=user).count():
    account = Account(user=user)
    account.save()
  
