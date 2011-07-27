from django.db import models
from django.contrib.auth.models import User, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from datetime import datetime
from settings import SITE_ROOT
from string import lower, replace

class Availability:
  '''
  This class is an enumeration for the availability statuses.
  '''
  Available, In_Stock, Unavailable = range(3)


class Acceptance:
  '''
  This class is an enumeration for the acceptance statuses.
  '''
  Rejected, Partially_Accepted, Accepted = range(3)


class DiffingMixin(object):
  '''
  this is a snippet from http://djangosnippets.org/snippets/1683/

  This class provides functions that add state monitoring to subclasses.
  '''
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
    url = SITE_ROOT + '/'
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
  mky_weight = models.FloatField('Weight', blank=True, null=True,
                                 help_text='The weight of the monkey.  This should be the weight at time of necropsy (or a recent weight if the necropsy has not yet occurred).')
  mky_drinking = models.BooleanField('Drinking', null=False,
                                     help_text='Was this monkey given alcohol?')
  mky_housing_control = models.BooleanField('Housing Control', null=False, default=False,
                                            help_text='Was this monkey part of a housing control group?')
  mky_necropsy_start_date = models.DateField('Necropsy Start Date', null=True, blank=True,
                                       help_text='Please enter the date the necropsy was performed on (or was started on).')
  mky_necropsy_start_date_comments = models.TextField('Necropsy Start Date Coments', null=True, blank=True)
  mky_necropsy_end_date = models.DateField('Necropsy End Date', null=True, blank=True,
                                       help_text='Please enter the end date of the necropsy.')
  mky_necropsy_end_date_comments = models.TextField('Necropsy End Date Coments', null=True, blank=True)
  mky_study_complete = models.BooleanField('Complete Study Performed', null=False,
                                           default=False,
                                           help_text='Did this monkey complete all stages of the experiment?')
  mky_stress_model = models.CharField('Stress Model', null=True, blank=True,
                                      max_length=30,
                                      help_text='This should indicate the grouping of the monkey if it was in a cohort that also tested stress models. (ex. MR, NR, HC, LC) ')
  mky_age_at_necropsy = models.CharField('Age at Necropsy', max_length=100, null=True, blank=True)
  
  def __unicode__(self):
    return str(self.mky_real_id)
  
  class Meta:
    db_table = 'mky_monkeys'


class Mta(models.Model):
  mta_id = models.AutoField(primary_key=True)
  user = models.ForeignKey(User, related_name='mta_set', db_column='usr_id', editable=False, blank=True)
  mta_date = models.DateField('Date Uploaded', editable=False, blank=True, null=True,
                              help_text='This is the Date that the MTA is uploaded.')
  mta_title = models.CharField('Title', blank=True, null=False, max_length=25,
                               help_text='Give your uploaded MTA a short unique name to make it easier for you to reference')
  mta_file = models.FileField(upload_to='mta/', default='', null=False, blank=False,
                              help_text='File to Upload')
  
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
  user = models.OneToOneField(User, related_name='account', db_column='usr_usr_id',
                              editable=False, blank=True, primary_key=True)
  act_shipping_name = models.CharField(max_length=25, null=True, blank=True,
                                       help_text="Your shipping name is required because it may be different from your username.")
  act_address1 = models.CharField(max_length=50, null=True, blank=True)
  act_address2 = models.CharField(max_length=50, null=True, blank=True)
  act_city = models.CharField(max_length=25, null=True, blank=True)
  act_state = models.CharField(max_length=2, null=True, blank=True)
  act_zip = models.CharField(max_length=10, null=True, blank=True)
  act_country = models.CharField(max_length=25, null=True, blank=True)
  act_fedex = models.CharField('FedEx', max_length=9, null=True, blank=True,
                               help_text="Your 9-digit FedEx Account number is required to ship tissues.")

  def __unicode__(self):
    return str(self.user.id)
   
  class Meta:
    db_table = 'act_account'


class DrinkingExperiment(models.Model):
  dex_id = models.AutoField('ID', primary_key=True)
  cohort = models.ForeignKey(Cohort, related_name='cohort_drinking_experiment_set', db_column='coh_cohort_id',
                             verbose_name='Cohort',
                             help_text='The cohort this experiment was performed on.')
  dex_date = models.DateField('Date',
                              help_text='The date this experiment was conducted.')
  dex_type = models.CharField('Experiment Type', max_length=100,
                              help_text='The type of experiment. (ex. 22 hour free access)')
  dex_notes = models.TextField('Notes', blank=True, null=True,
                               help_text='Use this space to enter anything about the experiment that does not fit in another field.')
  monkeys = models.ManyToManyField(Monkey, through='MonkeyToDrinkingExperiment')

  def __unicode__(self):
    return 'Experiment Type: ' + self.dex_type + ' Date: ' + str(self.dex_date) + ' Cohort: ' + str(self.cohort)


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


class TissueCategory(models.Model):
  cat_id = models.AutoField('ID', primary_key=True)
  cat_name = models.CharField('Name', max_length=100, unique=True, null=False,
                              help_text='The name of the tissue category.')
  cat_description = models.TextField('Description', null=True, blank=True,
                                     help_text='A description of the category.')
  parent_category = models.ForeignKey('self', verbose_name='Parent Category',
                                      default=None, null=True, blank=True,
                                      help_text='The parent category of this category.')
  cat_internal = models.BooleanField('Internal Use Only', default=True, null=False,
                             help_text='This value determines if tissues in this category can be ordered by users.')

  def __unicode__(self):
    return self.cat_name

  class Meta:
    db_table = 'cat_tissue_categories'


class TissueType(models.Model):
  tst_type_id = models.AutoField('ID', primary_key=True)
  category = models.ForeignKey(TissueCategory, verbose_name='Category',
                               db_column='cat_id',
                               null=False,
                               db_index=True)
  tst_tissue_name = models.CharField('Name', max_length=100, null=False,
                                     help_text='The name of the tissue type.')
  tst_description = models.TextField('Description', null=True,
                                     help_text='The description of the tissue type.')
  tst_count_per_monkey = models.IntegerField('Units per Monkey',
                                             blank=True,
                                             null=True,
                                             help_text='The maximum number of samples that can be harvested from a typical monkey.  Leave this blank if there is no limit.')
  unavailable_list = models.ManyToManyField(Monkey, db_table='ttu_tissue_types_unavailable',
                                          verbose_name='Unavailable For',
                                          related_name='unavailable_tissue_type_set',
                                          help_text='The monkeys this tissue type is not available for.')
  tst_cost = models.FloatField('Cost', default=0.0, null=False, blank=False)
  def __unicode__(self):
    return self.tst_tissue_name

  def get_stock(self, monkey):
    return self.tissue_sample_set.filter(monkey=monkey)

  def get_cohort_availability(self, cohort):
    for monkey in cohort.monkey_set.all():
      status = self.get_availability(monkey)
      # if the tissue is available for any monkey,
      # then it is available for the cohort
      if status == Availability.Available or \
         status == Availability.In_Stock:
         return True
    return False

  def get_availability(self, monkey):
    availability = Availability.Unavailable
    if monkey in self.unavailable_list.all():
      return availability

    # get the number of accepted, but not shipped, requests
    requests = TissueRequest.objects.filter(tissue_type=self,
                                             req_request__cohort=monkey.cohort,
                                             req_request__request_status=
                                             RequestStatus.objects.get(
                                               rqs_status_name='Accepted'))
    monkey_requests = list()
    for request in requests.all():
      # keep requests that are for this monkey
      if monkey in request.monkeys.all():
        monkey_requests.append(request)

    requested = len(monkey_requests)
    
    if monkey.cohort.coh_upcoming:
      # if there is a limit to the number of samples,
      # check if that limit has been reached
      if self.tst_count_per_monkey and (requested < self.tst_count_per_monkey):
        availability = Availability.Available
      elif self.tst_count_per_monkey is None:
        availability = Availability.Available
    else:
      # the tissues have been harvested, so check the inventory

      # get the number of tissues that have been harvested
      harvested_samples = TissueSample.objects.filter(monkey=monkey,
                                              tissue_type=self,).all()
      if len(harvested_samples) > 0:
        # tissues have been harvested, so we should use the inventories to determine if
        # the tissue is available.

        # get the tissues of this type for this monkey
        available_count = 0
        for sample in harvested_samples:
          available_count += sample.get_available_count()
        # check if the amount of stock exceeds the number of approved requests
        if requested < available_count:
          # if it does, the tissue is available (and in stock)
          availability = Availability.In_Stock
      elif self.tst_count_per_monkey and (requested < self.tst_count_per_monkey):
        # otherwise check if the limit has been reached
        availability = Availability.Available
      elif self.tst_count_per_monkey is None:
        availability = Availability.Available

    return availability

  def get_pending_request_count(self, monkey):
    return self.tissue_request_set.filter(\
      req_request__request_status=RequestStatus.objects.get(rqs_status_name='Submitted')).count()

  def get_accepted_request_count(self, monkey):
    return self.tissue_request_set.filter(\
      req_request__request_status=RequestStatus.objects.get(rqs_status_name='Accepted')).count()
  
  class Meta:
    db_table = 'tst_tissue_types'
    unique_together = (('tst_tissue_name', 'category'),)


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
  req_progress_agreement = models.BooleanField('I acknowledge that I will be required to submit a 90 day progress report on the tissue(s) that I have requested. In addition, I am willing to submit additional reports as required by the MATRR steering committee.',
                                               blank=False,
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
    return self.tissue_request_set.count()

  def get_requested_tissues(self):
    return self.tissue_request_set.all()

  def get_plan_name(self):
    plan = str(self.req_experimental_plan)
    plan = plan.replace('experimental_plans/', '', 1)
    return plan

  def save(self, force_insert=False, force_update=False, using=None):
    if self.request_status.rqs_status_id != self._original_state['request_status_id']\
        and self._original_state['request_status_id'] == RequestStatus.objects.get(rqs_status_name='Cart').rqs_status_id:
      self.req_request_date = datetime.now()
    self.req_modified_date = datetime.now()
    self._previous_status_id = self._original_state['request_status_id']
    super(Request, self).save(force_insert, force_update, using)
  
  class Meta:
    db_table = 'req_requests'


class TissueRequest(models.Model):
  rtt_tissue_request_id = models.AutoField(primary_key=True)
  req_request = models.ForeignKey(Request, null=False, related_name='tissue_request_set', db_column='req_request_id')
  tissue_type = models.ForeignKey(TissueType, null=False, related_name='tissue_request_set', db_column='tst_type_id')
  rtt_fix_type = models.CharField('Fixation', null=False, blank=False,
                                  max_length=200,
      help_text='Please select the appropriate fix type.')
  rtt_custom_increment = models.IntegerField('Custom Increment', default=0, editable=False, null=False)
  rtt_amount = models.FloatField('Amount',
      help_text='Please enter the amount of tissue you need.')
  unit = models.ForeignKey(Unit, null = False, related_name='+', db_column='unt_unit_id', 
      help_text='Please select the unit of measure.')
  rtt_notes = models.TextField('Notes', null=True, blank=True,
      help_text='Use this field to add any requirements that are not covered by the above form. You may also enter any comments you have on this particular tissue request.')
  monkeys = models.ManyToManyField(Monkey, db_table='mtr_monkeys_to_tissue_requests',
                                 verbose_name='Requested Monkeys',
                                 help_text='The monkeys this tissue is requested from.')
  accepted_monkeys = models.ManyToManyField(Monkey, db_table='atr_accepted_monkeys_to_tissue_requests',
                                 verbose_name='Accepted Monkeys',
                                 related_name='accepted_tissue_request_set',
                                 help_text='The accepted monkeys for this request.')

  def __unicode__(self):
    return self.tissue_type.tst_tissue_name + ': ' + self.rtt_fix_type

  def get_tissue(self):
    return self.tissue_type
  
  def has_notes(self):
    return self.rtt_notes is not None and self.rtt_notes != ''

  def get_notes(self):
    return self.rtt_notes

  def get_fix(self):
    return self.rtt_fix_type

  def get_amount(self):
    return str(self.rtt_amount) + self.unit.unt_unit_name

  def get_data(self):
    return [['Tissue Type', self.tissue_type],
            ['Fix', self.rtt_fix_type],
            ['Amount', str(self.rtt_amount) + self.unit.unt_unit_name]]

  def get_type_url(self):
    return self.tissue_type.category

  def get_reviews(self):
    return self.tissue_request_review_set.all()

  def get_html_label(self):
    label = self.tissue_type.tst_tissue_name + '_' + str(self.rtt_tissue_request_id)
    return replace(lower(label), ' ', '-')

  def get_accepted(self):
    count = self.accepted_monkeys.count()
    if count > 0:
      if count == self.monkeys.count():
        return Acceptance.Accepted
      else:
        return Acceptance.Partially_Accepted
    else:
      return Acceptance.Rejected

  def get_rejected_monkeys(self):
    return self.monkeys.exclude(mky_id__in=self.accepted_monkeys.all())

  class Meta:
    db_table = 'rtt_requests_to_tissue_types'
    unique_together = (('req_request', 'tissue_type', 'rtt_fix_type', 'rtt_custom_increment'),)


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
    return all( tissue_request.is_finished() for tissue_request in TissueRequestReview.objects.filter(review=self.rvs_review_id))
  
  class Meta:
    db_table = 'rvs_reviews'
    unique_together = ('user', 'req_request')


class TissueRequestReview(models.Model):
  vtr_request_review_id = models.AutoField(primary_key=True)
  review = models.ForeignKey(Review, null=False, related_name='tissue_request_review_set', db_column='rvs_review_id', editable=False)
  tissue_request = models.ForeignKey(TissueRequest, null=False, related_name='tissue_request_review_set', db_column='rtt_tissue_request_id', editable=False)
  vtr_scientific_merit = models.PositiveSmallIntegerField('Scientific Merit', null=True, blank=False,
                                                          choices=((0,0),(1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7),
                                                  (8,8), (9,9), (10, 10),),
      help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
  vtr_quantity = models.PositiveSmallIntegerField('Quantity', null=True, blank=False,
                                                  choices=((0,0),(1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7),
                                                  (8,8), (9,9), (10, 10),),
      help_text='Enter a number between 0 and 10, with 0 being the too little, 10 being too much, and 5 being an appropriate amount.')
  vtr_priority = models.PositiveSmallIntegerField('Priority', null=True, blank=False,
                                                  choices=((0,0),(1,1), (2,2), (3,3), (4,4), (5,5), (6,6), (7,7),
                                                  (8,8), (9,9), (10, 10),),
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
    return self.vtr_notes is not None and self.vtr_notes != ''

  def get_notes(self):
    return self.vtr_notes

  class Meta:
    db_table = 'vtr_reviews_to_tissue_requests'
    unique_together = ('review', 'tissue_request')


class Shipment(models.Model):
  shp_shipment_id = models.AutoField(primary_key=True)
  user = models.ForeignKey(User, null=False,
                           related_name='shipment_set')
  req_request = models.OneToOneField(Request, null=False,
                                  related_name='shipment')
  shp_tracking = models.CharField('Tracking Number', null=True, blank=True,
                                  max_length=100,
                                  help_text='Please enter the tracking number for this shipment.')
  shp_shipment_date = models.DateField('Shipped Date',
                                       blank=True,
                                       null=True,
                                       help_text='Please enter the date these tissues were shipped.')

  class Meta:
    db_table = 'shp_shipments'


class TissueSample(models.Model):
  tss_id = models.AutoField(primary_key=True)
  tissue_type = models.ForeignKey(TissueType, db_column='tst_type_id',
                                  related_name='tissue_sample_set',
                                  blank=False, null=False)
  monkey = models.ForeignKey(Monkey, db_column='mky_id',
                             related_name='tissue_sample_set',
                             blank=False, null=False)
  tss_freezer = models.CharField('Freezer Name',
                                 max_length=100,
                                 null=False,
                                 blank=False,
                                 help_text='Please enter the name of the freezer this sample is in.')
  tss_location = models.CharField('Location of Sample',
                                  max_length=100,
                                  null=False,
                                  blank=False,
                                  help_text='Please enter the location in the freezer where this sample is stored.')
  tss_details = models.TextField('Details',
                                  null=True,
                                  blank=True,
                                  help_text='Any extras details about this tissue sample.')
  tss_sample_count = models.IntegerField('Sample Count', null=False)
  tss_distributed_count = models.IntegerField('Distributed Count', null=False, default=0)
  tss_modified = models.DateTimeField('Last Updated', auto_now_add=True, editable=False, auto_now=True)

  def get_modified(self):
    return self.tss_modified

  def __unicode__(self):
    return str(self.monkey) + ' ' + str(self.tissue_type) + ' '  + self.tss_freezer \
           + ': ' + self.tss_location + ' (' + str(self.get_available_count()) + ')'

  def get_location(self):
    return self.tss_freezer + ': ' + self.tss_location

  def get_available_count(self):
    return self.tss_sample_count - self.tss_distributed_count

  class Meta:
    db_table = 'tss_tissue_samples'
    ordering = ['-monkey__mky_real_id', '-tissue_type__tst_tissue_name']


class Publication(models.Model):
  id = models.AutoField(primary_key=True)
  authors = models.TextField('Authors', null=True)
  title = models.CharField('Title', max_length=200, null=True)
  journal = models.CharField('Journal', max_length=200, null=True)
  cohorts = models.ManyToManyField(Cohort, db_table='ptc_publications_to_cohorts',
                                 verbose_name='Cohorts',
                                 related_name='publication_set',
                                 help_text='The cohorts involved in this publication.',
                                 null=True)
  published_year = models.CharField('Year Published', max_length=10, null=True)
  published_month = models.CharField('Month Published', max_length=10, null=True)
  issue = models.CharField('Issue Number', max_length=20, null=True)
  volume = models.CharField('Volume', max_length=20, null=True)
  pmid = models.IntegerField('PubMed ID', unique=True, null=True)
  pmcid = models.CharField('PubMed Central ID', max_length=20, null=True)
  isbn = models.IntegerField('ISBN', null=True)
  abstract = models.TextField('Abstract', null=True)
  keywords = models.TextField('Keywords', null=True)

  def __unicode__(self):
    return str(self.pmid)

  class Meta:
    db_table = 'pub_publications'


class GenBankSequence(models.Model):
  id = models.AutoField(primary_key=True)
  accession = models.CharField('Accession Number', max_length=20)
  cohort = models.ManyToManyField(Cohort, db_table='gtc_genbank_to_cohorts',
                                 verbose_name='Cohorts',
                                 related_name='genbank_set',
                                 help_text='The cohorts involved with this genbank sequence.')

  class Meta:
    db_table = 'gen_genbank_sequences'


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
    tissue_requests = TissueRequest.objects.filter(req_request=req_request.req_request_id)

    # for each committee member, create a new review for the request
    for user in committee_members:
      review = Review(req_request=req_request, user=user)
      review.save()
      # create a new TissueRequestReview for each TissueRequest
      for tissue_request in tissue_requests:
        TissueRequestReview(review=review, tissue_request=tissue_request).save()
  
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

