#encoding=utf-8
import os
import ast
import Image
import numpy
import dbarray
import settings
from django.core.files.base import File
from django.core.mail.message import EmailMessage
from django.db import models
from django.db.models import Q, Min, Max, Avg, Sum
from django.contrib.auth.models import User, Group, Permission
from django.db.models.query import QuerySet
from django.db.models.signals import post_save, pre_delete, pre_save
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from datetime import datetime, date, timedelta
from string import lower, replace
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError

def get_sentinel_user():
	return User.objects.get_or_create(username='deleted')[0]

def percentage_validator(value):
	MinValueValidator(0).__call__(value)
	MaxValueValidator(100).__call__(value)


class Enumeration(object):
	"""
		A small helper class for more readable enumerations,
		and compatible with Django's choice convention.
		You may just pass the instance of this class as the choices
		argument of model/form fields.

		Example:
			MY_ENUM = Enumeration([
				(100, 'MY_NAME', 'My verbose name'),
				(200, 'MY_AGE', 'My verbose age'),
			])
			assert MY_ENUM.MY_AGE == 100
			assert MY_ENUM[1] == (200, 'My verbose age')
		"""

	def __init__(self, enum_list):
		self.enum_list = [(item[0], item[2]) for item in enum_list]
		self.enum_dict = {}
		for item in enum_list:
			self.enum_dict[item[1]] = item[0]

	def __contains__(self, v):
		return (v in self.enum_list)

	def __len__(self):
		return len(self.enum_list)

	def __getitem__(self, v):
		if isinstance(v, basestring):
			return self.enum_dict[v]
		elif isinstance(v, int):
			return self.enum_list[v]

	def __getattr__(self, name):
		return self.enum_dict[name]

	def __iter__(self):
		return self.enum_list.__iter__()

InventoryStatus = (('Unverified', 'Unverified'), ('Sufficient', 'Sufficient'), ('Insufficient', 'Insufficient'))

#Units =  (('ul','μl'), ('ug','μg'), ('whole','whole'), ('mg','mg'), ('ml','ml'), ('g','g'))
#LatexUnits = {
#			'ul': '$\mu l$',
#			'ug': '$\mu g$',
#			'whole': '$whole$',
#			'mg': '$mg$',
#			'ml': '$ml$',
#			'g': '$g$',
#			}

Units = (('ul', 'μl'), ('ug', 'μg'), ('whole', 'whole'), ('mg', 'mg'), ('ml', 'ml'), ('g', 'g'), ('mm', 'mm'), ('cm', 'cm'))

ProteinUnits = (('mg/mL', 'mg/mL'), ('ng/mL', 'ng/mL'), ('ug/mL', 'μg/mL'), ('pg/mL', 'pg/mL'), ('uIU/mL', 'μIU/mL'), ('nmol/L', 'nmol/L'))

LatexUnits = {
	'ul': '$\mu l$',
	'ug': '$\mu g$',
	'whole': '$whole$',
	'mg': '$mg$',
	'ml': '$ml$',
	'g': '$g$',
	'cm': '$cm$',
	'mm': '$mm$',
	}

DexType = Enumeration([
	('O', 'OA', "Open Access"),
	('I', 'Ind', "Induction"),
])
DexTypes = tuple(i[1] for i in DexType) # uses of this should be replaced with DexType
DexTypesChoices = tuple((i, i) for i in DexTypes) # This should be removed once DexTypes is refactored to use DexType


ExperimentEventType = Enumeration([
	('D', 'Drink', 'Drink event'),
	('T', 'Time', 'Time event'),
	('P', 'Pellet', 'Pellet event'),
])

LeftRight = Enumeration([
						('L', 'Left', 'Left side'),
						('R', 'Right', 'Right side'),
						])

TissueTypeSexRelevant =  Enumeration([
						('F', 'Female', 'Female relevant tissue type'),
						('M', 'Male', 'Male relevant tissue type'),
						('B', 'Both', 'Sex independent tissue type'),
					])
RequestStatus =  Enumeration([
						('CA', 'Cart', 'Cart'),
						('RV', 'Revised', 'Revised'),
						('DP', 'Duplicated', 'Duplicated'),
						('SB', 'Submitted', 'Submitted'),
						('RJ', 'Rejected', 'Rejected'),
						('AC', 'Accepted', 'Accepted'),
						('PA', 'Partially', 'Partially accepted'),
						('SH', 'Shipped', 'Shipped'),
					])
VerificationStatus =  Enumeration([
						('CP', 'Complete', 'Complete'),
						('IC', 'Incomplete', 'Incomplete'),
					])
ResearchProgress = Enumeration([
	('NP', 'NoProgress', "No Progress"),
	("IP", 'InProgress', "In Progress"),
	("CP", 'Complete', "Complete"),
])


# These are the method names which ONLY VIP members can _see_
VIP_IMAGES_LIST = (
'monkey_etoh_bouts_drinks',
'monkey_etoh_bouts_drinks_intraday',
'monkey_etoh_first_max_bout',
'monkey_etoh_bouts_vol',
'monkey_bec_bubble',
'monkey_bec_consumption',
'monkey_bec_monthly_centroids',
'monkey_etoh_induction_cumsum',

'cohort_bec_maxbout',
'cohort_bec_firstbout',
'cohort_bec_firstbout_monkeycluster',
'cohort_etoh_induction_cumsum',
'cohort_etoh_gkg_quadbar',

'monkey_errorbox_etoh', # deprecated
'__vip',
'__brain_image',
)


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
				result[key] = {'old': value, 'new': self.__dict__.get(key, missing)}
		return result

Permission._meta.permissions = ([
	('issue_tracker', 'Can view link to issue tracker'),
	('upload_raw_data', 'Can upload MATRR data to server'),
])


class Institution(models.Model):
	ins_institution_id = models.AutoField('ins_id', primary_key=True)
	ins_institution_name = models.CharField('Institution', max_length=500, unique=True, null=False,
											help_text='Please enter the name of the institution.')

	def __unicode__(self):
		return self.ins_institution_name

	class Meta:
		db_table = 'ins_institutions'
		ordering = ['ins_institution_name']


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
	SPECIES = (('Rhesus', 'Rhesus'), ('Cyno', 'Cynomolgus'), ('Vervet', 'Vervet'))
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

	def has_protein_data(self):
		for monkey in self.monkey_set.all():
			if MonkeyProtein.objects.filter(monkey=monkey):
				return True
		return False

	def has_brain_images(self):
		if MonkeyImage.objects.filter(method='__brain_image', monkey__cohort=self).count():
			return True
		return False

	class Meta:
		db_table = 'coh_cohorts'


class CohortData(models.Model):
	cod_id = models.AutoField(primary_key=True)
	cohort = models.ForeignKey(Cohort, related_name='cod_set', db_column='coh_cohort_id', null=False, blank=False,
							   help_text='Choose a cohort associated with this file.')
	cod_title = models.CharField('Title', blank=True, null=False, max_length=35,
								 help_text='Brief description of this file.')
	cod_file = models.FileField('Selected file', upload_to='cod/', default='', null=False, blank=False,
								help_text='File to Upload')

	def __unicode__(self):
		return "%s: %s (%s)" % (self.cohort.__unicode__(), self.cod_title, self.cod_file.name)

	def verify_user_access_to_file(self, user):
		return user.is_authenticated()

	class Meta:
		db_table = 'cod_cohort_datafile'


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
	SEX_CHOICES = ( ('M', 'Male'), ('F', 'Female'))
	SPECIES = ( ('Rhesus', 'Rhesus'), ('Cyno', 'Cynomolgus'), ('Vervet', 'Vervet'))

	mky_id = models.AutoField('Monkey ID', primary_key=True)
	cohort = models.ForeignKey(Cohort, db_column='coh_cohort_id', verbose_name='Cohort',
							   help_text='The cohort this monkey belongs to.')
	mky_real_id = models.IntegerField('ID', unique=True,
									  help_text='The ID of the monkey.')
	mky_name = models.CharField('Name', max_length=100, blank=True, null=True,
								help_text='The monkey\'s name.')
	# Legacy note about the mky_gender field
	# It was decided sometime 2011 that 'gender' is an inaccurate representation of a monkey's sex.
	# It should (justly) be 'sex'.
	# This was decided after significant codebase and database population -.-
	# So, instead of a massively trivial refactoring of a single database field
	# We changed any public-facing use of this field to read 'sex', primarily in templates.
	# I have no intention of ever renaming this field.  -JF
	mky_gender = models.CharField('Sex', max_length=1, choices=SEX_CHOICES, blank=True, null=True,
								  help_text='The sex of the monkey.')
	mky_birthdate = models.DateField('Date of Birth', blank=True, null=True, max_length=20,
									 help_text='Please enter the date the monkey was born on.')
	mky_weight = models.FloatField('Weight', blank=True, null=True,
								   help_text='The weight of the monkey.  This should be the weight at time of necropsy (or a recent weight if the necropsy has not yet occurred).')
	mky_drinking = models.BooleanField('Is Drinking', null=False,
									   help_text='Was this monkey given alcohol?')
	mky_housing_control = models.BooleanField('Housing Control', null=False, default=False,
											  help_text='Was this monkey part of a housing control group?')
	mky_necropsy_start_date = models.DateField('Necropsy Start Date', null=True, blank=True,
											   help_text='Please enter the date the necropsy was performed on (or was started on).')
	mky_necropsy_start_date_comments = models.TextField('Necropsy Start Date Comments', null=True, blank=True)
	mky_necropsy_end_date = models.DateField('Necropsy End Date', null=True, blank=True,
											 help_text='Please enter the end date of the necropsy.')
	mky_necropsy_end_date_comments = models.TextField('Necropsy End Date Comments', null=True, blank=True)
	mky_study_complete = models.BooleanField('Complete Study Performed', null=False, default=False,
											 help_text='Did this monkey complete all stages of the experiment?')
	mky_stress_model = models.CharField('Stress Model', null=True, blank=True, max_length=30,
										help_text='This should indicate the grouping of the monkey if it was in a cohort that also tested stress models. (ex. MR, NR, HC, LC) ')
	mky_age_at_necropsy = models.CharField('Age at Necropsy', max_length=100, null=True, blank=True)
	mky_notes = models.CharField('Monkey Notes', null=True, blank=True, max_length=1000, )
	mky_species = models.CharField('Species', max_length=30, choices=SPECIES, help_text='Please select the species of the monkey.')
	mky_high_drinker = models.BooleanField("High-drinking monkey", null=False, blank=False, default=False)
	mky_low_drinker = models.BooleanField("Low-drinking monkey", null=False, blank=False, default=False)
	mky_age_at_intox = models.PositiveIntegerField("Age at first Intoxication (days)", null=True, blank=False, default=None)

	def __unicode__(self):
		return str(self.mky_id)

	def sex(self):
		if self.mky_gender == 'M':
			return u'Male'
		if self.mky_gender == 'F':
			return u'Female'

	def has_protein_data(self):
		if MonkeyProtein.objects.filter(monkey=self):
			return True
		return False

	def migrate_species(self, choices=SPECIES):
		for choice in choices:
			if choice[0] in self.cohort.coh_cohort_name:
				self.mky_species = choice[0]
				self.save()

	def populate_age_at_intox(self):
		becs = MonkeyBEC.objects.filter(monkey=self)
		if becs.count():
			becs = becs.filter(bec_mg_pct__gte=80).order_by('bec_collect_date')
			try:
				first_intox = becs[0]
			except IndexError:
				age = 0
			else:
				age = (first_intox.bec_collect_date.date() - self.mky_birthdate).days
			self.mky_age_at_intox = age
			self.save()

	class Meta:
		db_table = 'mky_monkeys'
		ordering = ['mky_id']
		permissions = ([
			('monkey_view_confidential', 'Can view confidential data'),
		])


class Mta(models.Model):
	########  BIG IMPORTANT WARNING  #######
	# If you're adding new fields to this model
	# Don't forget to exclude them from any applicable Form
	########
	mta_id = models.AutoField(primary_key=True)
	user = models.ForeignKey(User, related_name='mta_set', db_column='usr_id', editable=False, blank=True)
	mta_date = models.DateField('Date Uploaded', editable=False, blank=True, null=True,
								help_text='This is the Date that the MTA is uploaded.')
	mta_title = models.CharField('Title', blank=True, null=False, max_length=25,
								 help_text='Give your uploaded MTA a short unique name to make it easier for you to reference')
	mta_file = models.FileField(upload_to='mta/', default='', null=False, blank=False,
								help_text='File to Upload')
	mta_is_valid = models.BooleanField('MTA is Valid', null=False, blank=False, default=False)

	def __unicode__(self):
		return str(self.mta_id)

	def save(self, force_insert=False, force_update=False, using=None):
		self.mta_date = datetime.now()
		if self.mta_title is None:
			self.mta_title = self.mta_file.name
		super(Mta, self).save(force_insert, force_update, using)

	def verify_user_access_to_file(self, user):
		if self.user == user:
			return True
		if user.has_perm('matrr.view_mta_file'):
			return True
		return False


	class Meta:
		db_table = 'mta_material_transfer'
		permissions = (
		('view_mta_file', 'Can view MTA files of other users'),
		('receive_mta_request', 'Will receive MTA form requests'),
		('mta_upload_notification', 'Receive emails when MTAs uploaded'),
		)


class AccountManager(models.Manager):
	def users_with_perm(self, perm_string):
		try:
			p = Permission.objects.get(codename=perm_string)
		except:
			return Permission.objects.filter(codename=perm_string)
		users = p.user_set.all()
		groups = p.group_set.all()
		for group in groups:
			users |= group.user_set.all()
		return users.distinct()


class Account(models.Model):
	user = models.OneToOneField(User, related_name='account', db_column='usr_usr_id',
								editable=False, blank=True, primary_key=True)

	phone_number = models.CharField(max_length=10, blank=False)
	institution = models.CharField(max_length=60, blank=False)
	verified = models.BooleanField(default=False, blank=False, null=False)
	act_shipping_name = models.CharField(max_length=25, null=True, blank=True,
										 help_text="If you want to ship to different person, please fill his/her name as shipping name.")
	act_address1 = models.CharField('Shipping address 1', max_length=50, null=True, blank=True)
	act_address2 = models.CharField('Shipping address 2', max_length=50, null=True, blank=True)
	act_city = models.CharField('Shipping city', max_length=25, null=True, blank=True)
	act_state = models.CharField('Shipping state', max_length=2, null=True, blank=True)
	act_zip = models.CharField('Shipping ZIP', max_length=10, null=True, blank=True)
	act_country = models.CharField('Shipping country', max_length=25, null=True, blank=True)
	act_fedex = models.CharField('FedEx', max_length=9, null=True, blank=True,
								 help_text="Your 9-digit FedEx Account number is required to ship tissues.")
	act_real_address1 = models.CharField('Address 1', max_length=50, null=True, blank=False)
	act_real_address2 = models.CharField('Address 2', max_length=50, null=True, blank=True)
	act_real_city = models.CharField('City', max_length=25, null=True, blank=False)
	act_real_state = models.CharField('State', max_length=2, null=True, blank=False)
	act_real_zip = models.CharField('ZIP', max_length=10, null=True, blank=False)
	act_real_country = models.CharField('Country', max_length=25, null=True, blank=True)

	act_mta = models.CharField("MTA", max_length=500, null=True, blank=True)

	objects = AccountManager()

	username = ''
	first_name = ''
	last_name = ''
	email = ''

	def __init__(self, *args, **kwargs):
		super(Account, self).__init__(*args, **kwargs)
		if self.user:
			self.username = self.user.username
			self.first_name = self.user.first_name
			self.last_name = self.user.last_name
			self.email = self.user.email

	def __unicode__(self):
		return str(self.user.username) + ": " + self.user.first_name + " " + self.user.last_name

	def has_mta(self):
		# User uploaded a valid MTA
		for mta in self.user.mta_set.all():
			if mta.mta_is_valid:
				return True

		# User is member of UBMTA institution
		if self.act_mta:
			institution = Institution.objects.filter(ins_institution_name=self.act_mta)
			if institution and institution[0].ins_institution_name != "Non-UBMTA Institution":
				return True

		# In all other cases, user has no valid MTA
		return False

	def has_overdue_rud(self):
		requests = Request.objects.filter(user=self.user)
		for req in requests:
			if req.is_rud_overdue():
				return True
		return False

	def save(self, *args, **kwargs):
		super(Account, self).save(*args, **kwargs)


	class Meta:
		db_table = 'act_account'
		permissions = ([
			('view_other_accounts', 'Can view accounts of other users'),
			('view_etoh_data', 'Can view ethanol data'),
			('bcc_request_email', 'Receive BCC of processed request emails'),
			('po_manifest_email', 'Receive PO shipping manifest email'),
			('verify_mta', 'Can verify MTA uploads'),
		])


class DrinkingExperiment(models.Model):
	dex_id = models.AutoField('ID', primary_key=True)
	cohort = models.ForeignKey(Cohort, related_name='cohort_drinking_experiment_set', db_column='coh_cohort_id',
							   verbose_name='Cohort',
							   help_text='The cohort this experiment was performed on.')
	dex_date = models.DateField('Date',
								help_text='The date this experiment was conducted.')
	dex_type = models.CharField('Experiment Type', max_length=100,
								help_text='The type of experiment. (ex. "Open Access")')
	dex_notes = models.TextField('Notes', blank=True, null=True,
								 help_text='Use this space to enter anything about the experiment that does not fit in another field.')
	monkeys = models.ManyToManyField(Monkey, through='MonkeyToDrinkingExperiment')

	def __unicode__(self):
		return 'Experiment Type: ' + self.dex_type + ' Date: ' + str(self.dex_date) + ' Cohort: ' + str(self.cohort)


	class Meta:
		db_table = 'dex_drinking_experiments'


class MTDManager(models.Manager):
	def Ind(self):
		return self.get_query_set().filter(drinking_experiment__dex_type='Induction')

	def OA(self):
		return self.get_query_set().filter(drinking_experiment__dex_type='Open Access')


class MonkeyToDrinkingExperiment(models.Model):
	objects = MTDManager()
	mtd_id = models.AutoField(primary_key=True)
	monkey = models.ForeignKey(Monkey, null=False, related_name='mtd_set', db_column='mky_id', editable=False)
	drinking_experiment = models.ForeignKey(DrinkingExperiment, null=False, related_name='+', db_column='dex_id',
											editable=False)
	mtd_etoh_intake = models.FloatField('EtOH Intake', null=True, blank=True,
										help_text='Please enter the amount in mL of 4% EtOH consumed by the monkey.')
	mtd_veh_intake = models.FloatField('H2O Intake', null=True, blank=True,
									   help_text='Please enter the amount in mL of H2O consumed by the monkey.')
	mtd_total_pellets = models.IntegerField('Pellets Consumed', null=False, blank=False,
											help_text='Please enter the total number of pellets consumed by the monkey.')
	mtd_weight = models.FloatField('Weight', null=True, blank=True,
								   help_text='Please enter the weight of the monkey.')
	mtd_notes = models.TextField('Notes', blank=True, null=True,
								 help_text='Use this space to enter anything about the experiment that does not fit in another field.')
	mtd_pct_etoh = models.FloatField('EtOH %', blank=True, null=True, validators=[percentage_validator, ],
									 help_text='EtOH as a percentage of total drinking that day.')
	mtd_etoh_g_kg = models.FloatField('EtOH g/kg', blank=True, null=True,
									  help_text='EtOH grams per kilogram')
	mtd_etoh_bout = models.IntegerField('EtOH Bout', null=True, blank=True,
										help_text='Total etOH bouts (less than 300 seconds between consumption of etOH).')
	mtd_etoh_drink_bout = models.FloatField('EtOH Drink/Bout', blank=True, null=True,
											help_text='Average number of drinks (less than 5 seconds between consumption of etOH) per etOH bout')
	mtd_veh_bout = models.IntegerField('H2O Bout', blank=True, null=True,
									   help_text='Total H20 bouts (less than 300 seconds between consumption of H20)')
	mtd_veh_drink_bout = models.FloatField('H2O Drink/Bout', null=True, blank=True,
										   help_text='Average number of drinks (less than 5 seconds between consumption of H20) per H20 bout')
	mtd_etoh_conc = models.FloatField('EtOH Conc.', null=True, blank=True,
									  help_text='Ethanol concentration.')
	mtd_etoh_mean_drink_length = models.FloatField('EhOH Mean Drink Length', null=True, blank=True,
												   help_text='Mean length for ethanol drinks (less than 5 seconds between consumption of etOH is a continuous drink).')
	mtd_etoh_median_idi = models.FloatField('EtOH Media IDI', blank=True, null=True,
											help_text='Median time between drinks (always at least 5 seconds because 5 seconds between consumption defines a new drink).')
	mtd_etoh_mean_drink_vol = models.FloatField('EtOH Mean Drink Vol', null=True, blank=True,
												help_text='Mean volume of etOH drinks')
	mtd_etoh_mean_bout_length = models.FloatField('EtOH Mean Bout Length', null=True, blank=True,
												  help_text='Mean length for ethanol bouts (less than 300 seconds between consumption of etOH is a continuous bout)')
	mtd_etoh_media_ibi = models.FloatField('EtOH Median IBI', null=True, blank=True,
										   help_text='Median inter-bout interval (always at least 300 seconds, because 300 seconds between consumption defines a new bout)')
	mtd_etoh_mean_bout_vol = models.FloatField('EtOH Mean Bout Vol', null=True, blank=True,
											   help_text='Mean volume of ethanol bouts')
	mtd_etoh_st_1 = models.FloatField('EtOH St.1', blank=True, null=True,
									  help_text='Induction data (blank for 22 hour data): ethanol consumed during “State 1”, or the fixed pellet interval portion')
	mtd_etoh_st_2 = models.FloatField('EtOH St.2', blank=True, null=True,
									  help_text='Induction data (blank for 22 hour data):  ethanol consumed during “State 2”, or the pellet time-out between fixed pellet interval portion and the fixed ratio portion')
	mtd_etoh_st_3 = models.FloatField('EtOH St.3', blank=True, null=True,
									  help_text='Induction data (blank for 22 hour data):   ethanol consumed during “State 3”, or the fixed ratio portion, after pellet time out completed')
	mtd_veh_st_2 = models.FloatField('H2O St.2', blank=True, null=True,
									 help_text='Induction data (blank for 22 hour data):   H20 consumed during “State 2”, or the pellet time out portion')
	mtd_veh_st_3 = models.FloatField('H2O St.3', blank=True, null=True,
									 help_text='Induction data (blank for 22 hour data):   H20 consumed during “State 3”, or the fixed ratio portion')
	mtd_pellets_st_1 = models.IntegerField('Pellets St.1', blank=True, null=True,
										   help_text='Induction data (blank for 22 hour data): Pellets delivered during “State 1”')
	mtd_pellets_st_3 = models.IntegerField('Pellets St.3', blank=True, null=True,
										   help_text='Induction data (blank for 22 hour data): Pellets delivered during “State 3”')
	mtd_length_st_1 = models.IntegerField('Length St.1', blank=True, null=True,
										  help_text='Induction data (blank for 22 hour data): Length of “State 1”')
	mtd_length_st_2 = models.IntegerField('Length St.2', blank=True, null=True,
										  help_text='Induction data (blank for 22 hour data): Length of “State 2”')
	mtd_length_st_3 = models.IntegerField('Length St.3', blank=True, null=True,
										  help_text='Induction data (blank for 22 hour data): Length of “State 3”')
	mtd_vol_1st_bout = models.FloatField('Vol. 1st Bout', blank=True, null=True,
										 help_text='Volume of the first bout')
	mtd_pct_etoh_in_1st_bout = models.FloatField('% Etoh in First Bout', blank=True, null=True, validators=[percentage_validator, ],
												 help_text='Percentage of the day’s total etOH consumed in the first bout')
	mtd_drinks_1st_bout = models.IntegerField('# Drinks 1st Bout', blank=True, null=True,
											  help_text='Number of drinks in the first bout')
	mtd_mean_drink_vol_1st_bout = models.FloatField('Mean Drink Vol 1st Bout', blank=True, null=True,
													help_text='Mean drink volume of the first bout')
	mtd_fi_wo_drinking_st_1 = models.IntegerField('FI w/o Drinking St.1', blank=True, null=True,
												  help_text='Induction data (blank for 22 hour data): Number of fixed intervals without drinking in “State 1”')
	mtd_pct_fi_with_drinking_st_1 = models.FloatField('% Of FI with Drinking St.1', blank=True, null=True,
													  help_text='Induction data (blank for 22 hour data): Percentage of fixed intervals without drinking in “State 1”')
	mtd_latency_1st_drink = models.IntegerField('Latency to 1st Drink', blank=True, null=True,
												help_text='Time from session start to first etOH consumption')
	mtd_pct_exp_etoh = models.FloatField('Exp. EtOH %', blank=True, null=True, validators=[percentage_validator, ],
										 help_text='Experimental etOH percentage (left blank)')
	mtd_st_1_ioc_avg = models.FloatField('St. 1 IOC Avg', blank=True, null=True,
										 help_text='Induction data (blank for 22 hour data):  “State 1” Index of Curvature average')
	mtd_max_bout = models.IntegerField('Max Bout #', blank=True, null=True,
									   help_text='Number of the bout with maximum ethanol consumption')
	mtd_max_bout_start = models.IntegerField('Max Bout Start', blank=True, null=True,
											 help_text='Starting time in seconds of maximum bout (bout with largest ethanol consumption)')
	mtd_max_bout_end = models.IntegerField('Max Bout End', blank=True, null=True,
										   help_text='Ending time in seconds of maximum bout (bout with largest ethanol consumption)')
	mtd_max_bout_length = models.IntegerField('Max Bout Length', blank=True, null=True,
											  help_text='Length of maximum bout (bout with largest ethanol consumption)')
	mtd_max_bout_vol = models.FloatField('Max Bout Volume', blank=True, null=True,
										 help_text='Volume of maximum bout')
	mtd_pct_max_bout_vol_total_etoh = models.FloatField('% Etoh in Max Bout', blank=True, null=True,
														help_text='Maximum bout volume as a percentage of total ethanol consumed that day')

	# It might be ugly but being able to query this will speed up plotting.cohort_bihourly_etoh_treemap() a LOT
	mtd_pct_max_bout_vol_total_etoh_hour_0  = models.FloatField('Max Bout in 1st hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')
	mtd_pct_max_bout_vol_total_etoh_hour_1  = models.FloatField('Max Bout in 2nd hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')
	mtd_pct_max_bout_vol_total_etoh_hour_2  = models.FloatField('Max Bout in 3rd hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')
	mtd_pct_max_bout_vol_total_etoh_hour_3  = models.FloatField('Max Bout in 4th hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')
	mtd_pct_max_bout_vol_total_etoh_hour_4  = models.FloatField('Max Bout in 5th hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')
	mtd_pct_max_bout_vol_total_etoh_hour_5  = models.FloatField('Max Bout in 6th hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')
	mtd_pct_max_bout_vol_total_etoh_hour_6  = models.FloatField('Max Bout in 7th hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')
	mtd_pct_max_bout_vol_total_etoh_hour_7  = models.FloatField('Max Bout in 8th hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')
	mtd_pct_max_bout_vol_total_etoh_hour_8  = models.FloatField('Max Bout in 9th hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')
	mtd_pct_max_bout_vol_total_etoh_hour_9  = models.FloatField('Max Bout in 10th hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')
	mtd_pct_max_bout_vol_total_etoh_hour_10 = models.FloatField('Max Bout in 11th hour, as Volume % of Total Etoh', blank=True, null=True, help_text='Bihourly maximum bout volume as a percentage of total ethanol consumed that day')

	mtd_seconds_to_stageone = models.IntegerField('Stage One Time (s)', blank=False, null=True, default=None,
												  help_text="Seconds it took for monkey to reach day's ethanol allotment")

	def __unicode__(self):
		return str(self.drinking_experiment) + ' Monkey: ' + str(self.monkey)

	def get_etoh_ratio(self):
		return self.mtd_etoh_intake * 0.4 / self.mtd_weight

	def populate_max_bout_hours(self):
		hour_const = 0
		experiment_len = 22

		block_len = 2

		for hour_start in range(hour_const,hour_const + experiment_len, block_len ):
			hour_end = hour_start + block_len
			fraction_start = (hour_start-hour_const)*60*60
			fraction_end = (hour_end-hour_const)*60*60

			bouts_in_fraction = self.bouts_set.filter(ebt_start_time__gte=fraction_start, ebt_start_time__lte=fraction_end)

			if self.mtd_etoh_intake > 0:
				try:
					max_bout = 1.* bouts_in_fraction.order_by('-ebt_volume')[0].ebt_volume / self.mtd_etoh_intake
				except:
					max_bout = None
			else:
				max_bout = None
			field_name = "mtd_pct_max_bout_vol_total_etoh_hour_%d" % (hour_start/2)
			self.__setattr__(field_name, max_bout)
			self.save()

	def populate_mtd_seconds_to_stageone(self):
		if self.drinking_experiment.dex_type == 'Open Access':
			self.mtd_seconds_to_stageone = 0
		else:
			dex_date = self.drinking_experiment.dex_date
			eevs = ExperimentEvent.objects.filter(monkey=self.monkey, eev_occurred__year=dex_date.year, eev_occurred__month=dex_date.month, eev_occurred__day=dex_date.day)
			eevs = eevs.exclude(eev_etoh_volume=None).order_by('-eev_occurred')
			try:
				eev = eevs[0]
			except IndexError:
				self.mtd_seconds_to_stageone = -1
			else:
				self.mtd_seconds_to_stageone = eev.eev_session_time
		self.save()

	class Meta:
		db_table = 'mtd_monkeys_to_drinking_experiments'


class ExperimentBout(models.Model):
	ebt_id = models.AutoField(primary_key=True)
	mtd = models.ForeignKey(MonkeyToDrinkingExperiment, null=False, db_column='mtd_id', related_name='bouts_set')
	ebt_number = models.PositiveIntegerField('Bout number', blank=False, null=False)
	ebt_start_time = models.PositiveIntegerField('Start time [s]', blank=False, null=False)
	ebt_end_time = models.PositiveIntegerField('End time [s]', blank=False, null=False)
	ebt_length = models.PositiveIntegerField('Bout length [s]', blank=False, null=False)
	ebt_ibi = models.PositiveIntegerField('Inter-Bout Interval [s]', blank=True, null=True)
	ebt_volume = models.FloatField('Bout volume [ml]', blank=False, null=False)

	ebt_pct_vol_total_etoh = models.FloatField('Bout Volume as % of Total Etoh', blank=True, null=True, help_text="Bout's volume as a percentage of total ethanol consumed that day")

	def populate_pct_vol_total_etoh(self, recalculate=False):
		if recalculate or not self.ebt_pct_vol_total_etoh:
			_pct = self.ebt_volume / self.mtd.mtd_etoh_intake
			self.ebt_pct_vol_total_etoh = _pct if _pct > 0 else None
			self.save()


	def clean(self):
		if self.ebt_end_time < self.ebt_start_time:
			raise ValidationError('End time cannot be lower that Start time')

		if self.ebt_end_time - self.ebt_start_time != self.ebt_length or self.ebt_end_time == self.ebt_start_time:
			#		An isolated bout is given the length of 1 second, despite start time and end time being equal. 
			if  self.ebt_end_time == self.ebt_start_time and self.ebt_length == 1:
				return
			raise ValidationError('Bout length does not correspond the Start and End time. An isolated drink is given the length of 1 second, despite start time and end time being equal.')

	class Meta:
		db_table = 'ebt_experiment_bouts'


class ExperimentDrink(models.Model):
	edr_id = models.AutoField(primary_key=True)
	ebt = models.ForeignKey(ExperimentBout, null=False, db_column='ebt_id', related_name='drinks_set')
	edr_number = models.PositiveIntegerField('Drink number', blank=False, null=False)
	edr_start_time = models.PositiveIntegerField('Start time [s]', blank=False, null=False)
	edr_end_time = models.PositiveIntegerField('End time [s]', blank=False, null=False)
	edr_length = models.PositiveIntegerField('Drink length [s]', blank=False, null=False)
	edr_idi = models.PositiveIntegerField('Inter-Drink Interval [s]', blank=True, null=True)
	edr_volume = models.FloatField('Bout volume [ml]', blank=False, null=False)

	def clean(self):
		if self.edr_end_time < self.edr_start_time:
			raise ValidationError('End time cannot be lower that Start time')

		if self.edr_end_time - self.edr_start_time != self.edr_length or self.edr_end_time == self.edr_start_time:
			#		An isolated drink is given the length of 1 second, despite start time and end time being equal. 
			if  self.edr_end_time == self.edr_start_time and self.edr_length == 1:
				return
			raise ValidationError('Drink length does not correspond to Start and End time. (An isolated drink is given the length of 1 second, despite start time and end time being equal.)')

	class Meta:
		db_table = 'edr_experiment_drinks'


class ExperimentEvent(models.Model):
	eev_id = models.AutoField(primary_key=True)
	monkey = models.ForeignKey(Monkey, related_name='event_set', db_column='mky_id', editable=False)
	dex_type = models.CharField('Experiment Type', choices=DexTypesChoices, max_length=100, help_text='The type of experiment. (ex. "Open Access")')
	eev_source_row_number = models.PositiveIntegerField('Source file row number', blank=False, null=False)
	eev_occurred = models.DateTimeField('Event occurred', blank=False, null=False)
	eev_dose = models.FloatField('Dose', blank=False, null=False)
	eev_panel = models.PositiveIntegerField('Panel', null=False, blank=False)
	eev_fixed_time = models.PositiveIntegerField('Fixed time [s]', blank=True, null=True)
	eev_experiment_state = models.IntegerField('Induction experiment state', validators=[MaxValueValidator(3), MinValueValidator(0)], blank=False, null=False)
	eev_event_type = models.CharField('Event type (Time/Pellet/Drink)', max_length=1, choices=ExperimentEventType, blank=False, null=False)
	eev_session_time = models.PositiveIntegerField('Session time [s]', blank=False, null=False)
	eev_segement_time = models.PositiveIntegerField('Segment time [s]', blank=False, null=False)
	eev_pellet_time = models.PositiveIntegerField('Pellet time [s]', blank=False, null=False)
	eev_etoh_side = models.CharField('EtOH side (Right/Left)', max_length=1, choices=LeftRight, blank=True, null=True)
	eev_etoh_volume = models.FloatField('EtOH volume of most recent drink', blank=True, null=True)
	eev_etoh_total = models.FloatField('EtOH total volume', blank=True, null=True)
	eev_etoh_elapsed_time_since_last = models.PositiveIntegerField('Elapsed time since last etOh drink [s]', blank=True, null=True)
	eev_veh_side = models.CharField('H20 side (Right/Left)', max_length=1, choices=LeftRight, blank=True, null=True)
	eev_veh_volume = models.FloatField('H20 volume of most recent drink', blank=True, null=True)
	eev_veh_total = models.FloatField('H20 total volume', blank=True, null=True)
	eev_veh_elapsed_time_since_last = models.PositiveIntegerField('Elapsed time since last H20 drink [s]', blank=True, null=True)
	eev_scale_string = models.CharField('Original string data from scale', max_length=50, blank=True, null=True)
	eev_hand_in_bar = models.BooleanField('Hand in bar', blank=False, null=False)
	eev_blank = models.IntegerField('This should be blank but I found some values', blank=True, null=True)
	eev_etoh_bout_number = models.PositiveIntegerField('EtOh bout number', blank=True, null=True)
	eev_etoh_drink_number = models.PositiveIntegerField('EtOh drink number', blank=True, null=True)
	eev_veh_bout_number = models.PositiveIntegerField('H20 bout number', blank=True, null=True)
	eev_veh_drink_number = models.PositiveIntegerField('H20 drink number', blank=True, null=True)
	eev_timing_comment = models.CharField('Timing comment or possibly post pellet flag', max_length=50, blank=True, null=True)

	eev_pellet_elapsed_time_since_last = models.PositiveIntegerField('Elapsed time since last pellet [s]', blank=True, null=True)

	def populate_time_since_pellet(self, recalculate=False):
		if not self.eev_pellet_elapsed_time_since_last or recalculate:
			current = self.eev_occurred
			previous_events = ExperimentEvent.objects.filter(eev_occurred__lt=current).order_by('eev_occurred')
			previous_pellets = previous_events.filter(eev_event_type=ExperimentEventType.Pellet)
			pellet_max = previous_pellets.aggregate(Max('eev_occurred'))['eev_occurred__max']
			time_diff = current-pellet_max
			self.eev_pellet_elapsed_time_since_last = time_diff.seconds
			self.save()

	class Meta:
		db_table = 'eev_experiment_events'


class MonkeyException(models.Model):
	mex_id = models.AutoField(primary_key=True)
	monkey = models.ForeignKey(Monkey, related_name='exception_set', db_column='mky_id', editable=False)
	mex_stage = models.CharField('Experiment Type', choices=DexType, max_length=1, help_text='The stage of the experiment')
	mex_date = models.DateField('Exception Date', blank=False, null=False)
	mex_file_corrected = models.BooleanField("File Errors Corrected", default=False)
	mex_excluded = models.BooleanField("Day not used at all", default=False)
	mex_lifetime = models.BooleanField("Day used for lifetime intake only", default=False)
	mex_2pct = models.BooleanField("Monkey given .02 conc ethanol", default=False)
	mex_etoh_intake = models.FloatField("Ethanol Intake", blank=False, null=False, default=0, help_text="Need to find out from steve _exactly_ what this is.")

	def purge_own_data(self, delete_mtd=False, delete_bec=False, delete_eev=False, render_images=True, delete_for_serious=False):
		if delete_mtd:
			mtds = MonkeyToDrinkingExperiment.objects.filter(monkey=self.monkey, drinking_experiment__dex_date=self.mex_date)
			if delete_for_serious:
				mtds.delete()
			elif mtds.count():
				print "%d mtd records would have been deleted." % mtds.count()
		if delete_bec:
			becs = MonkeyBEC.objects.filter(monkey=self.monkey, bec_collect_date__year=self.mex_date.year, bec_collect_date__month=self.mex_date.month, bec_collect_date__day=self.mex_date.day)
			if delete_for_serious:
				becs.delete()
			elif becs.count():
				print "%d bec records would have been deleted." % becs.count()
		if delete_eev:
			eevs = ExperimentEvent.objects.filter(monkey=self.monkey, eev_occurred__year=self.mex_date.year, eev_occurred__month=self.mex_date.month, eev_occurred__day=self.mex_date.day)
			if delete_for_serious:
				eevs.delete()
			elif eevs.count():
				print "%d eev records would have been deleted." % eevs.count()
		if (delete_mtd or delete_bec or delete_eev) and render_images:
			for mig in MonkeyImage.objects.filter(monkey=self.monkey):
				mig.save(force_render=True)


	def clean(self):
		if not (self.mex_file_corrected or self.mex_excluded or self.mex_lifetime or self.mex_2pct):
			raise ValidationError('Exception records must have an exception')

	class Meta:
		db_table = 'mex_monkey_exception'


class NecropsySummary(models.Model):
	ncm_id = models.AutoField(primary_key=True)
	monkey = models.OneToOneField(Monkey, null=False, db_column='ebt_id', related_name='necropsy_summary')
	ncm_age_onset_etoh = models.CharField("Age at Ethanol Onset", max_length=100, blank=True, null=True)
	ncm_etoh_onset = models.DateTimeField("Date of Ethanol Onset", blank=True, null=True)
	ncm_6_mo_start = models.DateField('6 Month Start', blank=True, null=True)
	ncm_6_mo_end = models.DateField('6 Month End', blank=True, null=True)
	ncm_12_mo_end = models.DateField('12 Month End', blank=True, null=True)
	ncm_etoh_4pct_induction = models.FloatField("Induction Ethanol Intake", blank=True, null=True)
	ncm_etoh_4pct_22hr = models.FloatField("22hr Free Access Ethanol Intake", blank=True, null=True)
	ncm_etoh_4pct_lifetime = models.FloatField("Lifetime Ethanol Intake (in 4% ml)", blank=True, null=True)
	ncm_etoh_g_lifetime = models.FloatField("Lifetime Etanol Intake (in grams)", blank=True, null=True)
	ncm_sum_g_per_kg_induction = models.FloatField("Induction Ethanol Intake (g-etoh per kg-weight)", blank=True, null=True)
	ncm_sum_g_per_kg_22hr = models.FloatField("22hr Free Access Ethanol Intake (g-etoh per kg-weight)", blank=True, null=True)
	ncm_sum_g_per_kg_lifetime = models.FloatField("Lifetime Ethanol Intake (g-etoh per kg-weight)", blank=True, null=True)
	ncm_22hr_6mo_avg_g_per_kg = models.FloatField("22hr 6mo average Ethanol Intake (g-etoh per kg-weight)", blank=True, null=True)
	ncm_22hr_2nd_6mos_avg_g_per_kg = models.FloatField("22hr 6mo average Ethanol Intake 2nd (g-etoh per kg-weight)", blank=True, null=True)
	ncm_22hr_12mo_avg_g_per_kg = models.FloatField("22hr 12mo average Ethanol Intake (g-etoh per kg-weight)", blank=True, null=True)

	class Meta:
		db_table = 'ncm_necropsy_summary'


class VIPQuerySet(models.query.QuerySet):
	def vip_filter(self, user):
		if user.has_perm('matrr.view_vip_images'):
			return self
		else:
			return self.exclude(method__in=VIP_IMAGES_LIST)


class VIPManager(models.Manager):
	def get_query_set(self):
		return VIPQuerySet(self.model, using=self._db)

	def vip_filter(self, user):
		return self.get_query_set().vip_filter(user)


#  This model breaks MATRR field name scheme
class MATRRImage(models.Model):
	modified = models.DateTimeField('Last Modified', auto_now_add=True, editable=False, auto_now=True)
	title = models.CharField('Title', blank=True, null=False, max_length=500, help_text='Brief description of this image.')
	method = models.CharField('Method', blank=True, null=False, max_length=150, help_text='The method used to generate this image.')
	parameters = models.CharField('Parameters', blank=True, null=False, max_length=1500, editable=False, default='defaults', help_text="The method's parameters used to generate this image.")
	image = models.ImageField('Image', upload_to='matrr_images/', default='', null=False, blank=False)
	svg_image = models.ImageField('Image', upload_to='matrr_images/', default='', null=False, blank=False)
	thumbnail = models.ImageField('Thumbnail Image', upload_to='matrr_images/', default='', null=True, blank=True)
	html_fragment = models.FileField('HTML Fragement', upload_to='matrr_images/fragments/', null=True, blank=False)
	canonical = models.BooleanField("MATRR Canonical Image", blank=False, null=False, default=False)

	thumbnail_size = (240, 240)
	objects = VIPManager()

	def _construct_filefields(self, mpl_figure, data_map, *args, **kwargs):
		# export the image and thumbnail to a temp folder and save them to the self.ImageFields
		if mpl_figure:
			image, thumbnail, svg_image_path = self._draw_image(mpl_figure)
			self.image = File(open(image, 'r'))
			self.thumbnail = File(open(thumbnail, 'r'))
			self.svg_image = File(open(svg_image_path, 'r'))
			# generate the html fragment for the image and save it
			if data_map:
				self.save() # must be called before html frag gets built, or else the image paths are still in /tmp
				html_frag_path = self._build_html_fragment(data_map)
				html_frag = open(html_frag_path, 'r')
				self.html_fragment = File(html_frag)

			self.save()
		else:
			self.delete()

	def _plot_picker(self):
		#  This needs to be overridden by subclasses
		return

	def _draw_image(self, mpl_figure):
		DPI = mpl_figure.get_dpi()

		filename = '/tmp/' + str(self)
		image_path = filename + '.png'
		thumb_path = filename + '-thumb.jpg'
		svg_image_path = filename + '.svg'
		mpl_figure.savefig(image_path, dpi=DPI)
		mpl_figure.savefig(svg_image_path, format='svg', dpi=DPI)

		image_file = Image.open(image_path)
		image_file.thumbnail(self.thumbnail_size, Image.ANTIALIAS)
		image_file.save(thumb_path)

		return image_path, thumb_path, svg_image_path

	def _build_html_fragment(self, data_map, add_footer=True, save_fragment=False):
		import collections
		from django.template.context import Context
		from django.template.loader import get_template

		fragment_path = '/tmp/%s.html' % str(self)

		data_map = data_map if isinstance(data_map, collections.Iterable) else False
		t = get_template('html_fragments/%s.html' % self.method) # templates will be named identical to the plotting method
		c = Context({'map': data_map, 'image': self, 'bigWidth': self.image.width * 1.1, 'bigHeight': self.image.height * 1.1})
#		print self.__class__.name
		foot_t = get_template('html_fragments/fragment_foot.html')
		foot_c = Context({'html_fragment': str(self).replace(" ", "_").replace('(', "").replace(")",""),
						 'class': self.__class__.__name__, 'imageID': self.pk,
						 'map': data_map })

		html_fragment = open(fragment_path, 'w+')
		html_fragment.write(str(t.render(c)))
		if add_footer:
			html_fragment.write(str(foot_t.render(foot_c)))
		html_fragment.flush()
		html_fragment.close()

		if save_fragment: # Most of the MATRRImage framework saves the fragment in _construct_filefields.  This overrides that, primarily for brain images
			self.html_fragment = File(open(fragment_path, 'r'))
			self.save()
		return fragment_path


	def verify_user_access_to_file(self, user):
		if self.method in VIP_IMAGES_LIST:
			return user.is_authenticated() and user.account.verified and user.has_perm('matrr.view_vip_images')
		return user.is_authenticated() and user.account.verified

	def frag(self):
		return os.path.basename(self.html_fragment.name)

	def __unicode__(self):
		# Subclasses should override this method too
		return "%s.(%s)" % (self.title, 'MATRRImage')

	def populate_svg(self):
		return

	class Meta:
		abstract = True


#  This model breaks MATRR field name scheme
class MTDImage(MATRRImage):
	mdi_id = models.AutoField(primary_key=True)
	monkey_to_drinking_experiment = models.ForeignKey(MonkeyToDrinkingExperiment, null=False, related_name='image_set', editable=False)

	def _construct_filefields(self, *args, **kwargs):
		# fetch the plotting method and build the figure, map
		spiffy_method = self._plot_picker()
		if self.parameters == 'defaults' or self.parameters == '':
			mpl_figure, data_map = spiffy_method(mtd=self.monkey_to_drinking_experiment)
		else:
			params = ast.literal_eval(self.parameters)
			mpl_figure, data_map = spiffy_method(mtd=self.monkey_to_drinking_experiment, **params)

		super(MTDImage, self)._construct_filefields(mpl_figure, data_map)

	def _plot_picker(self):
		from utils import plotting

		PLOTS = plotting.MONKEY_PLOTS

		if not self.method:
			return "My plot method field has not been populated.  I don't know what I am."
		if not self.method in PLOTS:
			return "My method field doesn't match any keys in plotting.MONKEY_PLOTS"

		return PLOTS[self.method][0]

	def save(self, force_render=False, *args, **kwargs):
		super(MTDImage, self).save(*args, **kwargs) # Can cause integrity error if not called first.
		if self.monkey_to_drinking_experiment and self.method and self.title:
			if not self.image or force_render:
				self._construct_filefields()

	def __unicode__(self):
		return "MTDImage.%s.(%s)" % (self.title, str(self.pk))

	class Meta:
		db_table = 'mdi_mtd_image'


#  This model breaks MATRR field name scheme
class MonkeyImage(MATRRImage):
	mig_id = models.AutoField(primary_key=True)
	monkey = models.ForeignKey(Monkey, null=False, related_name='image_set', editable=False)

	def _construct_filefields(self, *args, **kwargs):
		# fetch the plotting method and build the figure, map
		spiffy_method = self._plot_picker()
		if self.parameters == 'defaults' or self.parameters == '':
			mpl_figure, data_map = spiffy_method(monkey=self.monkey)
		else:
			params = ast.literal_eval(self.parameters)
			mpl_figure, data_map = spiffy_method(monkey=self.monkey, **params)

		super(MonkeyImage, self)._construct_filefields(mpl_figure, data_map)

	def _plot_picker(self):
		from utils import plotting

		PLOTS = plotting.MONKEY_PLOTS

		if not self.method:
			return "My plot method field has not been populated.  I don't know what I am."
		if not self.method in PLOTS:
			return "My method field doesn't match any keys in plotting.MONKEY_PLOTS"

		return PLOTS[self.method][0]

	def save(self, force_render=False, *args, **kwargs):
		super(MonkeyImage, self).save(*args, **kwargs) # Can cause integrity error if not called first.
		if self.monkey and self.method and self.title:
			if not self.image or force_render:
				self._construct_filefields()

	def __unicode__(self):
		if self.method == '__brain_image':
			return "%s.%s.(%s)" % (self.monkey.__unicode__(), "BrainImage", str(self.pk))
		title = "".join(x for x in self.title if x.isalnum())
		return "%s.%s.(%s)" % (self.monkey.__unicode__(), title, str(self.pk))

	class Meta:
		permissions = (
			('view_vip_images', 'Can view VIP images'),
			)
		db_table = 'mig_monkey_image'


#  This model breaks MATRR field name scheme
class CohortImage(MATRRImage):
	cig_id = models.AutoField(primary_key=True)
	cohort = models.ForeignKey(Cohort, null=False, related_name='image_set', editable=False)

	def _construct_filefields(self, *args, **kwargs):
		# fetch the plotting method and build the figure, map
		spiffy_method = self._plot_picker()
		if self.parameters == 'defaults' or self.parameters == '':
			mpl_figure, data_map = spiffy_method(cohort=self.cohort)
		else:
			params = ast.literal_eval(self.parameters)
			mpl_figure, data_map = spiffy_method(cohort=self.cohort, **params)

		super(CohortImage, self)._construct_filefields(mpl_figure, data_map)

	def _plot_picker(self):
		from utils import plotting

		PLOTS = plotting.COHORT_PLOTS

		if not self.method:
			return "My plot method field has not been populated.  I don't know what I am."
		if not self.method in PLOTS:
			return "My method field doesn't match any keys in plotting.COHORT_PLOTS"

		return PLOTS[self.method][0]

	def save(self, force_render=False, *args, **kwargs):
		super(CohortImage, self).save(*args, **kwargs) # Can cause integrity error if not called first.
		if self.cohort and self.method and self.title:
			if not self.image or force_render:
				self._construct_filefields()

	def __unicode__(self):
		return "%s.%s.(%s)" % (self.cohort.__unicode__(), self.title, str(self.pk))

	class Meta:
		db_table = 'cig_cohort_image'


#  This model breaks MATRR field name scheme
class CohortProteinImage(MATRRImage):
	cpi_id = models.AutoField(primary_key=True)
	cohort = models.ForeignKey(Cohort, null=False, related_name='pci_image_set', editable=False)
	protein = models.ForeignKey("Protein", null=False, related_name='pci_image_set', editable=False)
	# this model does not use MATRRImage.parameters

	def _construct_filefields(self, *args, **kwargs):
		# fetch the plotting method and build the figure, map
		spiffy_method = self._plot_picker()
		mpl_figure, data_map = spiffy_method(cohort=self.cohort, protein=self.protein)

		super(CohortProteinImage, self)._construct_filefields(mpl_figure, data_map)

	def _plot_picker(self):
		from utils import plotting

		PLOTS = plotting.COHORT_PLOTS

		if not self.method:
			return "My plot method field has not been populated.  I don't know what I am."
		if not self.method in PLOTS:
			return "My method field doesn't match any keys in plotting.COHORT_PLOTS"

		return PLOTS[self.method][0]

	def save(self, force_render=False, *args, **kwargs):
		super(CohortProteinImage, self).save(*args, **kwargs) # Can cause integrity error if not called first.
		if self.cohort and self.protein:
			if not self.image or force_render:
				self.method = 'cohort_protein_boxplot'
				self.title = '%s : %s' % (str(self.cohort), str(self.protein.pro_abbrev))
				self._construct_filefields()

	def __unicode__(self):
		return "%s: %s.%s" % (str(self.pk), str(self.cohort), str(self.protein))

	class Meta:
		db_table = 'cpi_cohort_protein_image'


#  This model breaks MATRR field name scheme
class MonkeyProteinImage(MATRRImage):
	mpi_id = models.AutoField(primary_key=True)
	monkey = models.ForeignKey(Monkey, null=False, related_name='mpi_image_set', editable=False)
	proteins = models.ManyToManyField('Protein', null=False, related_name='mpi_image_set', editable=False)

	def _construct_filefields(self, *args, **kwargs):
		# fetch the plotting method and build the figure, map
		spiffy_method = self._plot_picker()

		if self.parameters == 'defaults' or self.parameters == '':
			mpl_figure, data_map = spiffy_method(monkey=self.monkey, proteins=self.proteins.all())
		else:
			params = ast.literal_eval(self.parameters)
			mpl_figure, data_map = spiffy_method(monkey=self.monkey, proteins=self.proteins.all(), **params)

		super(MonkeyProteinImage, self)._construct_filefields(mpl_figure, data_map)

	def _plot_picker(self):
		from utils import plotting

		PLOTS = plotting.MONKEY_PLOTS

		if not self.method:
			return "My plot method field has not been populated.  I don't know what I am."
		if not self.method in PLOTS:
			return "My method field doesn't match any keys in plotting.MONKEY_PLOTS"

		return PLOTS[self.method][0]

	def save(self, force_render=False, *args, **kwargs):
		super(MonkeyProteinImage, self).save(*args, **kwargs) # Can cause integrity error if not called first.
		if self.monkey and self.proteins.all().count() and self.method:
			if not self.image or force_render:
				self.title = '%s : %s' % (str(self.monkey), ",".join(self.proteins.all().values_list('pro_abbrev',flat=True)))
				self._construct_filefields()

	def __unicode__(self):
		return "%s- %s" % (str(self.pk), str(self.monkey))

	class Meta:
		db_table = 'mpi_monkey_protein_image'


class DataFile(models.Model):
	dat_id = models.AutoField(primary_key=True)
	account = models.ForeignKey(Account, null=True)
	dat_modified = models.DateTimeField('Last Modified', auto_now_add=True, editable=False, auto_now=True)
	dat_title = models.CharField('Title', blank=True, null=False, max_length=50, help_text='Brief description of this data file.')
	dat_data_file = models.FileField('Data File', upload_to='data_files/', null=True, blank=False)

	def verify_user_access_to_file(self, user):
		return user.is_authenticated() and user.account.verified and user.account == self.account

	def __unicode__(self):
		# You should override this method too
		return "%s- %s" % (self.account.username, self.dat_title)

	class Meta:
		db_table = 'dat_data_file'


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
									   blank=True,
									   help_text='The description of the tissue type.')
	tst_count_per_monkey = models.IntegerField('Units per Monkey',
											   blank=True,
											   null=True,
											   help_text='The maximum number of samples that can be harvested from a typical monkey.  Leave this blank if there is no limit.')
	unavailable_list = models.ManyToManyField(Monkey, db_table='ttu_tissue_types_unavailable',
											  verbose_name='Unavailable For',
											  related_name='unavailable_tissue_type_set',
											  blank=True,
											  help_text='The monkeys this tissue type is not available for.')
	tst_cost = models.FloatField('Cost', default=0.00)
	tst_sex_relevant = models.CharField('Sex relevant tissue type', max_length=1, choices=TissueTypeSexRelevant, default=TissueTypeSexRelevant.Both)

	def __unicode__(self):
		return self.tst_tissue_name

	def get_stock(self, monkey):
		return self.tissue_sample_set.filter(monkey=monkey)

	def get_cohort_availability(self, cohort):
		if 'custom' in self.tst_tissue_name.lower():
			return True
		for monkey in cohort.monkey_set.all():
			status = self.get_monkey_availability(monkey)
			# if the tissue is available for any monkey,
			# then it is available for the cohort
			if status == Availability.Available or\
			   status == Availability.In_Stock:
				return True
		return False

	def get_directly_in_stock_available_monkey_ids(self):
		tss = TissueSample.objects.filter(tissue_type=self).filter(Q(tss_sample_quantity__gt=0) | Q(tss_sample_quantity=None))
		monkey_ids = tss.values_list('monkey', flat=True)

		return monkey_ids

	def get_monkey_from_coh_upcoming_availability(self, monkey):
		if self.tst_sex_relevant != TissueTypeSexRelevant.Both:
			if monkey.mky_gender != self.tst_sex_relevant:
				return Availability.Unavailable
		return Availability.Available

	def get_monkey_availability(self, monkey):
		if 'custom' in self.tst_tissue_name.lower():
			return Availability.Available
		if self.tst_sex_relevant != TissueTypeSexRelevant.Both:
			if monkey.mky_gender != self.tst_sex_relevant:
				return Availability.Unavailable

		if monkey.cohort.coh_upcoming:
		#			just idea: is possible a situation when we know that some tissue of this monkey will never be in stock?
		# 			if yes, we should probably track it somehow and reflect here, but not important right now
			return Availability.Available

		tissue_samples = TissueSample.objects.filter(monkey=monkey, tissue_type=self) # should return 1 result, always.
		for tissue_sample in tissue_samples:
			return tissue_sample.get_availability()

		return Availability.Unavailable

	def get_pending_request_count(self, monkey):
		return self.tissue_request_set.filter(req_request__req_status=RequestStatus.Submitted).count()

	def get_accepted_request_count(self, monkey):
		return self.tissue_request_set.filter(req_request__req_status=RequestStatus.Accepted).count()

	class Meta:
		db_table = 'tst_tissue_types'
		unique_together = (('tst_tissue_name', 'category'),)
		ordering = ['tst_tissue_name']
		permissions = (
		('browse_inventory', 'Can browse inventory'),
		)


class RequestManager(models.Manager):
	def processed(self):
		return self.get_query_set()\
		.exclude(req_status=RequestStatus.Cart)\
		.exclude(req_status=RequestStatus.Revised)\
		.exclude(req_status=RequestStatus.Duplicated)

	def evaluated(self):
		return self.get_query_set()\
		.exclude(req_status=RequestStatus.Cart)\
		.exclude(req_status=RequestStatus.Revised)\
		.exclude(req_status=RequestStatus.Duplicated)\
		.exclude(req_status=RequestStatus.Submitted)

	def revised(self):
		return self.get_query_set().filter(req_status=RequestStatus.Revised)

	def duplicated(self):
		return self.get_query_set().filter(req_status=RequestStatus.Duplicated)

	def revised_or_duplicated(self):
		return self.get_query_set().filter(Q(req_status=RequestStatus.Revised) | Q(req_status=RequestStatus.Duplicated))

	def submitted(self):
		return self.get_query_set().filter(req_status=RequestStatus.Submitted)

	def shipped(self):
		return self.get_query_set().filter(req_status=RequestStatus.Shipped)

	def accepted_and_partially(self):
		return self.get_query_set().filter(Q(req_status=RequestStatus.Accepted) | Q(req_status=RequestStatus.Partially))

	def cart(self):
		return self.get_query_set().filter(req_status=RequestStatus.Cart)


class Request(models.Model, DiffingMixin):
	REFERRAL_CHOICES = (
	('Internet Search', 'Internet Search'),
	('Publication', 'Publication'),
	('Professional Meeting', 'Professional Meeting'),
	('MATRR Staff/Investigator', 'MATRR Staff/Investigator'),
	('Colleague', 'Colleague'),
	('other', 'other'),
	)
	objects = RequestManager()
	req_request_id = models.AutoField('ID', primary_key=True)
	parent_request = models.ForeignKey('Request', null=True, editable=False, related_name='revised_request_set')
	req_status = models.CharField('Request Status', max_length=2, choices=RequestStatus, null=False, blank=False, default=RequestStatus.Cart)
	cohort = models.ForeignKey(Cohort, null=False, db_column='coh_cohort_id', editable=False, )
	user = models.ForeignKey(User, null=False, db_column='usr_user_id', editable=False, )
	req_modified_date = models.DateTimeField(auto_now_add=True, editable=False, auto_now=True)
	req_request_date = models.DateTimeField(editable=False, auto_now_add=True)
	req_experimental_plan = models.FileField('Experimental Plan', upload_to='experimental_plans/',
											 default='', null=True, blank=True,
											 help_text='You may upload a detailed description of your research plans for the tissues you are requesting.')
	req_project_title = models.CharField('Project Title', null=False, blank=False,
										 max_length=200,
										 help_text='The name of the project or proposal these tissues will be used in.')
	req_reason = models.TextField('Purpose of Tissue Request', null=False, blank=False,
								  help_text='Please provide a short paragraph describing the hypothesis and methods proposed.')
	req_funding = models.TextField('Source of Funding', null=True, blank=False,
								   help_text='Please describe the source of funding which will be used for this request.')
	req_progress_agreement = models.BooleanField(
		'I acknowledge that I will be required to submit a 90 day progress report on the tissue(s) that I have requested. In addition, I am willing to submit additional reports as required by the MATRR steering committee.'
		,
		blank=False,
		null=False, )
	req_safety_agreement = models.BooleanField(
		'I acknowledge that I have read and understand the potential biohazards associated with tissue shipment.'
		,
		blank=False,
		null=False, )
	req_referred_by = models.CharField('How did you hear about the tissue bank?',
									   choices=REFERRAL_CHOICES,
									   null=False,
									   max_length=100)
	req_notes = models.TextField('Request Notes', null=True, blank=True)
	req_report_asked = models.BooleanField('Progress report asked', default=False)
	req_report_asked_count = models.IntegerField('Progress report requested count', default=0)

	def _migrate_report_count(self):
		if not self.req_report_asked_count and self.req_report_asked:
			self.req_report_asked_count = 1
			self.save()

	req_purchase_order = models.CharField("Purchase Order", max_length=200, null=True, blank=True)

	def __unicode__(self):
		return 'Request: %d' % self.pk + \
			   ' User: ' + self.user.username +\
			   ' Cohort: ' + self.cohort.coh_cohort_name +\
			   ' Date: ' + self.req_request_date.strftime("%I:%M%p  %m/%d/%y")

	def verify_user_access_to_file(self, user):
		if self.user == user:
			return True
		if user.has_perm('matrr.view_experimental_plan'):
			return True
		return False

	def print_self_in_detail(self):
		return "Request: %d\nProject title: %s\nRequested: %s\nCohort: %s\nRequest reason: %s\nNotes: %s" % (self.pk, self.req_project_title,
																								str(self.req_request_date), self.cohort.coh_cohort_name, self.req_reason,
																								self.req_notes or "None")

	def get_shipments(self):
		return Shipment.objects.filter(req_request=self)

	def get_requested_tissue_count(self):
		return self.tissue_request_set.count()

	def get_requested_tissues(self):
		return self.tissue_request_set.all()

	def get_plan_name(self):
		plan = str(self.req_experimental_plan)
		plan = plan.replace('experimental_plans/', '', 1)
		return plan

	def get_total_estimated_cost(self):
		total = 0
		for item in self.tissue_request_set.all():
			total += item.get_estimated_cost()
#		return self.req_estimated_cost if self.req_estimated_cost != None else total
		return total

	def get_tiv_collisions(self):
		tissue_requests = self.tissue_request_set.all()
		collisions = TissueInventoryVerification.objects.none()
		for tissue_request in tissue_requests:
			collisions |= tissue_request.get_tiv_collisions()
		return collisions

	def get_rtt_collisions(self):
		colliding_tissue_requests = TissueRequest.objects.none()
		for tissue_request in self.tissue_request_set.all():
			colliding_tissue_requests |= tissue_request.get_rtt_collisions()
		return colliding_tissue_requests

	def __get_tiv_collision_request(self, collisions):
		collision_requests = set()
		for collision in collisions:
			if collision.tissue_request.req_request != self:
				collision_requests.add(collision.tissue_request.req_request)
		return collision_requests

	def __get_rtt_collision_request(self, collisions):
		collision_requests = set()
		for collision in collisions:
			if collision.req_request != self:
				collision_requests.add(collision.req_request)

		return collision_requests

	def __duplicate(self, cohort, is_revision=False):
		kwargs = {}
		# this does not capture m2m fields or other models with FK refs to Request
		for field in self._meta.fields:
			if field.name != 'req_request_id': # do not duplicate the primary key
				kwargs[field.name] = self.__getattribute__(field.name)
		revised = Request.objects.create(**kwargs)
		# Don't duplicate some other fields
		revised.cohort = cohort
		revised.req_modified_date = datetime.now()
		revised.req_status = RequestStatus.Revised if is_revision else RequestStatus.Duplicated
		revised.req_report_asked = False
		revised.parent_request = self

		# Duplicate all TissueRequests
		revised.save() # save() must be called before the forloop and m2m assignment
		tr_duplicates = []
		for tissue_request in self.tissue_request_set.all():
			fully_accepted = tissue_request.is_fully_accepted()
			if is_revision and not fully_accepted: # for revised requests, do not duplicate fully accepted tissue requests
				tr_duplicates.append(tissue_request.create_revised_duplicate(revised)) # update monkey fields
			if not is_revision: # for duplicate requests, duplicate everything
				tr_duplicates.append(tissue_request.create_duplicate(revised)) # clear monkey fields and populate with new cohort

		revised.tissue_request_set.add(*tr_duplicates)
		revised.req_estimated_cost = None
		revised.save()
		return revised

	def create_revised_duplicate(self):
		return self.__duplicate(self.cohort, is_revision=True)

	def create_duplicate(self, cohort):
		return self.__duplicate(cohort, is_revision=False)

	def get_sub_req_collisions_for_monkey(self, monkey):
		collisions = self.get_tiv_collisions()
		collisions = collisions.filter(tissue_request__req_request__req_status=RequestStatus.Submitted, monkey=monkey)
		return self.__get_tiv_collision_request(collisions)

	def get_sub_req_collisions(self):
		collisions = self.get_tiv_collisions()
		collisions = collisions.filter(tissue_request__req_request__req_status=RequestStatus.Submitted)
		return self.__get_tiv_collision_request(collisions)

	def get_acc_req_collisions(self):
		collisions = self.get_rtt_collisions()
		collisions = collisions.filter(Q(req_request__req_status=RequestStatus.Accepted) | Q(req_request__req_status=RequestStatus.Partially))
		return self.__get_rtt_collision_request(collisions)

	def get_acc_req_collisions_for_tissuetype_monkey(self, tissue_type, monkey):
		collisions = self.get_rtt_collisions()
		collisions = collisions.filter(Q(req_request__req_status=RequestStatus.Accepted) | Q(req_request__req_status=RequestStatus.Partially))
		collisions = collisions.filter(tissue_type=tissue_type, accepted_monkeys__in=[monkey])
		return self.__get_rtt_collision_request(collisions)

	def save(self, force_insert=False, force_update=False, using=None):
		if self.req_status != self._original_state['req_status']\
		and (self._original_state['req_status'] == RequestStatus.Cart or
			 self._original_state['req_status'] == RequestStatus.Revised or
			 self._original_state['req_status'] == RequestStatus.Duplicated):
			self.req_request_date = datetime.now()
		self.req_modified_date = datetime.now()
		self._previous_status = self._original_state['req_status']
		super(Request, self).save(force_insert, force_update, using)

	def can_be_revised(self):
		if self.req_status == RequestStatus.Rejected or self.req_status == RequestStatus.Partially:
			return True
		return False

	def can_be_duplicated(self):
		if self.req_status != RequestStatus.Cart:
#			allow_dupe = True
#			for rtt in self.tissue_request_set.all():
#				if rtt.accepted_monkeys.all(): # only test tissues with accepted monkeys.  Rejected tissues won't be duplicated anyway
#					allow_dupe = allow_dupe and (rtt.accepted_monkeys.all().count() == self.cohort.monkey_set.all().count())
#			return allow_dupe
			return True
		return False

	def can_be_edited(self):
		if self.req_status in  (RequestStatus.Duplicated, RequestStatus.Revised):
			return True
		return False

	def is_processed(self):
		if not self.req_status in (RequestStatus.Cart, RequestStatus.Revised, RequestStatus.Duplicated):
			return True
		return False

	def is_evaluated(self):
		if self.req_status == RequestStatus.Accepted or self.req_status == RequestStatus.Partially\
		   or self.req_status == RequestStatus.Rejected or self.req_status == RequestStatus.Shipped:
			return True
		return False

	def is_shipped(self):
		if self.req_status == RequestStatus.Shipped:
			return True
		return False

	def has_collisions(self):
		acc_collisions = self.get_acc_req_collisions()
		sub_collisions = self.get_sub_req_collisions()
		if acc_collisions or sub_collisions:
			return True
		return False

	def has_pending_shipment(self):
		for rtt in self.tissue_request_set.exclude(accepted_monkeys=None):
			if not rtt.shipment:
				return True
		return False

	def is_missing_shipments(self):
		for rtt in self.tissue_request_set.exclude(accepted_monkeys=None):
			if not rtt.shipment:
				return True
		return False

	def can_be_evaluated(self):
		if self.req_status == RequestStatus.Submitted:
			return True
		return False

	def can_be_shipped(self):
		if self.req_status == RequestStatus.Accepted or self.req_status == RequestStatus.Partially:
			if self.user.account.has_mta() and self.req_purchase_order and not self.user.account.has_overdue_rud():
				return True
		return False

	def submit_request(self):
		self.req_status = RequestStatus.Submitted

	def ship_request(self):
		fully_shipped = True
		for tr in self.tissue_request_set.all():
			if tr.shipment is None or tr.shipment.shp_shipment_date is None:
				fully_shipped = False
				break

		if fully_shipped:
			self.req_status = RequestStatus.Shipped
			self.save()

	def get_inventory_verification_status(self):
		for rtt in self.tissue_request_set.all():
			if rtt.get_inventory_verification_status() == VerificationStatus.Incomplete:
				return VerificationStatus.Incomplete
		return VerificationStatus.Complete

	def get_max_shipment(self):
		try:
			return self.shipments.all().order_by('-shp_shipment_date')[0]
		except IndexError:
			return ''

	def is_rud_overdue(self):
		return self.get_rud_weeks_overdue() > 0

	def get_rud_weeks_overdue(self):
		today = date.today()
		grace_period = 0
		try:
			if self.rud_set.filter(rud_progress=ResearchProgress.Complete).count():
				return 0
			latest_rud = self.rud_set.order_by('-rud_date')[0]
			age = (today - latest_rud.rud_date).days
			if latest_rud.rud_progress == ResearchProgress.NoProgress:
				grace_period = 45
			if latest_rud.rud_progress == ResearchProgress.InProgress:
				grace_period = 90
		except IndexError:
			max_shipment = self.get_max_shipment()
			if not max_shipment or not max_shipment.shp_shipment_date:
				return 0 # nothing shipped yet
			age = (today - max_shipment.shp_shipment_date).days
			grace_period = 90

		age_overdue = age - grace_period
		weeks_overdue = int(age_overdue / 7)
		return weeks_overdue

	def get_overdue_rud_color(self):
		weeks_overdue = self.get_rud_weeks_overdue()
		if weeks_overdue >= 3:
			return 'red'
		elif weeks_overdue <= 0:
			return ''
		else:
			return 'orange'

	class Meta:
		db_table = 'req_requests'
		permissions = (
		('view_experimental_plan', 'Can view experimental plans of other users'),
		('can_receive_colliding_requests_info', 'Can receive colliding requests info'),
		)


class Shipment(models.Model):
	shp_shipment_id = models.AutoField(primary_key=True)
	user = models.ForeignKey(User, null=False,
							 related_name='shipment_set')
	req_request = models.ForeignKey(Request, null=False,
									   related_name='shipments')
	shp_tracking = models.CharField('Tracking Number', null=True, blank=True,
									max_length=100,
									help_text='Please enter the tracking number for this shipment.')
	shp_shipment_date = models.DateField('Shipped Date',
										 blank=True,
										 null=True,
										 help_text='The date these tissues were shipped.')

	def get_tissue_requests(self):
		return TissueRequest.objects.filter(shipment=self)

	class Meta:
		db_table = 'shp_shipments'


class ResearchUpdate(models.Model):
	rud_id = models.AutoField(primary_key=True)
	req_request = models.ForeignKey(Request, related_name='rud_set', db_column='req_id', null=False, blank=False, help_text='Choose a shipped request for which you would like to upload a research update:')
	rud_date = models.DateField('Date updated', editable=False, blank=False, null=False, auto_now_add=True)
	rud_progress = models.CharField("Research Progress", choices=ResearchProgress, max_length=5, blank=False, null=False, default='IP')
	rud_pmid = models.CharField("PMID", max_length=20, blank=True, null=False, default='')
	rud_data_available = models.BooleanField("Data Available", help_text="Data is available for upload to MATRR.  Please contact me to arrange this integration into the MATRR.")
	rud_comments = models.TextField("Comments", blank=True, null=False)
	rud_file = models.FileField('Research Update', upload_to='rud/', default='', null=False, blank=False, help_text='File to Upload')
	rud_grant = models.TextField("Grant Information", blank=True, null=False, help_text="Description of grant submissions resulting from the MATRR tissues")

	def __unicode__(self):
		_pmid = " (%s)" % self.rud_pmid if self.rud_pmid else ''
		return "%s: %s%s" % (str(self.req_request), self.rud_progress, _pmid)

	def publication_url(self):
		return "http://www.ncbi.nlm.nih.gov/pubmed?term=%s" % self.rud_pmid

	def verify_user_access_to_file(self, user):
		if self.req_request.user == user:
			return True
		if user.has_perm('matrr.view_rud_detail'):
			return True
		return False

	class Meta:
		db_table = 'rud_research_update'
		permissions = (
		('view_rud_detail', 'Can view research updates of other users.'),
		)


class TissueRequest(models.Model):
	rtt_tissue_request_id = models.AutoField(primary_key=True)
	req_request = models.ForeignKey(Request, null=False, related_name='tissue_request_set', db_column='req_request_id')
	tissue_type = models.ForeignKey(TissueType, null=False, related_name='tissue_request_set', db_column='tst_type_id')
	rtt_fix_type = models.CharField('Fixation', null=False, blank=False,
									max_length=200,
									help_text='Please select the appropriate fix type.')
	rtt_prep_type = models.CharField('Preparation', null=False, blank=False,
									max_length=200,
									help_text='Please select the appropriate prep type.')
	# the custom increment is here to allow us to have a unique constraint that prevents duplicate requests
	# for a tissue in a single order while allowing multiple custom requests in an order.
	rtt_custom_increment = models.IntegerField('Custom Increment', default=0, editable=False, null=False)
	rtt_amount = models.FloatField('Amount', help_text='Please enter the amount of tissue you need.')
	rtt_units = models.CharField('Amount units',
								 choices=Units, null=False, max_length=20, default=Units[0][0])
	rtt_notes = models.TextField('Tissue Notes', null=True, blank=True,
								 help_text='Use this field to add any requirements that are not covered by the above form. You may also enter any comments you have on this particular tissue request.')
	monkeys = models.ManyToManyField(Monkey, db_table='mtr_monkeys_to_tissue_requests',
									 verbose_name='Requested Monkeys',
									 help_text='The monkeys this tissue is requested from.')
	accepted_monkeys = models.ManyToManyField(Monkey, db_table='atr_accepted_monkeys_to_tissue_requests', blank=True, null=True,
											  verbose_name='Accepted Monkeys',
											  related_name='accepted_tissue_request_set',
											  help_text='The accepted monkeys for this request.')

	previously_accepted_monkeys = models.ManyToManyField(Monkey, db_table='atr_previously_accepted_monkeys_to_tissue_requests', blank=True, null=True,
														 verbose_name='Previously Accepted Monkeys',
														 related_name='previously_accepted_tissue_request_set',
														 help_text='The accepted monkeys for the original of this request (applicable only if created as revised).')

	shipment = models.ForeignKey(Shipment, null=True, blank=True, on_delete=models.SET_NULL, related_name='tissue_request_set', db_column='shp_shipment_id')
	# IMPORTANT: shipment's on_delete needs to == models.SET_NULL.  If not, when you delete a shipment on the web page, you delete the tissue request with it (muy no bueno).
	rtt_estimated_cost = models.IntegerField("Estimated cost", null=True, blank=True)

	def is_partially_accepted(self):
		return self.accepted_monkeys.count() != 0

	def is_fully_accepted(self):
		return self.monkeys.count() == self.accepted_monkeys.count()

	def __unicode__(self):
		return "%s - %s - %s" % (str(self.req_request.cohort), self.tissue_type.tst_tissue_name, self.rtt_fix_type)

	def get_tissue(self):
		return self.tissue_type

	def has_notes(self):
		return self.rtt_notes is not None and self.rtt_notes != ''

	def get_notes(self):
		return self.rtt_notes

	def get_fix(self):
		return self.rtt_fix_type

	def get_amount(self):
		return str(self.rtt_amount) + ' ' + self.get_rtt_units_display().encode('UTF-8')

	def get_latex_amount(self):
		return str(self.rtt_amount) + ' ' + LatexUnits[self.rtt_units]

	def get_data(self):
		return [['Tissue Type', self.tissue_type],
				['Fix', self.rtt_fix_type],
				['Prep', self.rtt_prep_type],
				['Amount', self.get_amount()],
				['Estimated Cost', "$%.2f" % self.get_estimated_cost()]
				]

	def get_latex_data(self):
		return [['Tissue Type', self.tissue_type],
			['Fix', self.rtt_fix_type],
			['Amount', self.get_latex_amount()],
			['Estimated Cost', "$%.2f" % self.get_estimated_cost()]]

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

	def get_estimated_cost(self):
		brain = 250		#  Base brain tissue cost
		peripheral = 100	#  Base peripheral tissue cost
		special = 100	#  Cost for special fixation

		monkey_cost = 0
		if self.rtt_fix_type != "Flash Frozen" or self.rtt_prep_type != 'Tissue':
			monkey_cost += special
		if "Brain" in self.tissue_type.category.cat_name:
			monkey_cost += brain
		elif "Peripheral" in self.tissue_type.category.cat_name:
			monkey_cost += peripheral
		else:
			monkey_cost += (brain + peripheral) * .5

		if self.accepted_monkeys.all():
			estimated_cost = monkey_cost * self.accepted_monkeys.count()
		else:
			estimated_cost = monkey_cost * self.monkeys.count()

		return estimated_cost if self.rtt_estimated_cost is None else self.rtt_estimated_cost

	def get_tiv_collisions(self):
		other_tivs = TissueInventoryVerification.objects.exclude(tissue_request=self.rtt_tissue_request_id).exclude(tissue_request=None)

		tiv_collisions = TissueInventoryVerification.objects.none()
		for monkey in self.monkeys.all():
			tiv_collisions |= other_tivs.filter(monkey=monkey, tissue_type=self.tissue_type)

		tiv_collisions = tiv_collisions.distinct()
		return tiv_collisions

	def get_rtt_collisions(self):
		other_rtts = TissueRequest.objects.exclude(pk=self.pk)
		rtt_collisions = other_rtts.filter(tissue_type=self.tissue_type, monkeys__in=self.monkeys.all())
		return rtt_collisions

	def get_inventory_verification_status(self):
		tivs = TissueInventoryVerification.objects.filter(tissue_request=self)
		for tiv in tivs:
			if tiv.tiv_inventory == "Unverified":
				return VerificationStatus.Incomplete
		return VerificationStatus.Complete

	def create_revised_duplicate(self, revised_request):
		revised = TissueRequest() # I don't know why this worked for TissueRequest but not Request
		# this does not capture M2M fields or other models with FK refs to TissueRequest
		for field in self._meta.fields:
			if field.name != 'rtt_tissue_request_id': # do not copy the primary key
				revised.__setattr__(field.name, self.__getattribute__(field.name))

		# Update the request FK with the new revised request
		revised.req_request = revised_request
		revised.rtt_estimated_cost = None
		# And copy the requested and accepted monkeys
		revised.save() # Must have a PK before doing m2m stuff
		for a in self.accepted_monkeys.all():
			revised.previously_accepted_monkeys.add(a)
		revised.accepted_monkeys.clear()
		if self.is_partially_accepted():
			monk = list()
			for m in self.monkeys.all():
				if m not in self.accepted_monkeys.all():
					monk.append(m)
			revised.monkeys = monk
		else:
			revised.monkeys = self.monkeys.all()

		revised.save()
		return revised

	def create_duplicate(self, revised_request):
		revised = TissueRequest() # I don't know why this worked for TissueRequest but not Request
		# this does not capture M2M fields or other models with FK refs to TissueRequest
		for field in self._meta.fields:
			if field.name != 'rtt_tissue_request_id': # do not copy the primary key
				revised.__setattr__(field.name, self.__getattribute__(field.name))

		# Update the request FK with the new revised request
		revised.req_request = revised_request
		revised.rtt_estimated_cost = None
		# And clear the requested and accepted monkeys
		revised.save() # Must have a PK before doing m2m stuff
		revised.accepted_monkeys.clear()
		revised.previously_accepted_monkeys.clear()
		revised.monkeys.clear()
		revised.monkeys.add(*revised_request.cohort.monkey_set.all())
		revised.save()
		return revised

	def cart_display(self):
		return self.tissue_type.tst_tissue_name

	def _migrate_fix_prep(self):
		if self.rtt_fix_type == 'RNA':
			self.rtt_prep_type = u'RNA'
		else:
			self.rtt_prep_type = u'Tissue'
		self.save()

	def save(self, *args, **kwargs):
		super(TissueRequest, self).save(*args, **kwargs)
		if self.rtt_tissue_request_id is None and self.tissue_type.category.cat_name == 'Custom':
			# if this is a custom request and it hasn't been saved yet
			# set the increment to the correct amount
			self.rtt_custom_increment = TissueRequest.objects.filter(req_request=self.req_request,
																	 tissue_type__category__cat_name='Custom').count()

	class Meta:
		db_table = 'rtt_requests_to_tissue_types'
		#unique_together = (('req_request', 'tissue_type', 'rtt_prep_type', 'rtt_custom_increment'),)


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
		if 'assay' in self.req_request.cohort.coh_cohort_name.lower():
			if self.user.username != 'jdaunais':
				return True

		return all(tissue_request.is_finished() for tissue_request in TissueRequestReview.objects.filter(
			review=self.rvs_review_id))

	class Meta:
		permissions = (
			('can_receive_pending_reviews_info', 'Can receive pending reviews info by e-mail'),
			('view_review_overview', 'Can view review overview and history overview')
			)
		db_table = 'rvs_reviews'
		unique_together = ('user', 'req_request')


class TissueRequestReview(models.Model):
	vtr_request_review_id = models.AutoField(primary_key=True)
	review = models.ForeignKey(Review, null=False, related_name='tissue_request_review_set', db_column='rvs_review_id',
							   editable=False)
	tissue_request = models.ForeignKey(TissueRequest, null=False, related_name='tissue_request_review_set',
									   db_column='rtt_tissue_request_id', editable=False)
	vtr_scientific_merit = models.PositiveSmallIntegerField('Scientific Merit', null=True, blank=False,
															choices=(
															(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6),
															(7, 7),
															(8, 8), (9, 9), (10, 10),),
															help_text='Enter a number between 0 and 10, with 0 being no merit and 10 being the highest merit.')
	vtr_quantity = models.CharField('Quantity', null=True, blank=False, max_length=12,
									choices=(
									("Too little", "Too little"), ("Appropriate", "Appropriate"), ("Too much", "Too much"),),
									help_text='Select a choice which best describes the amount of tissue requested.')
	vtr_priority = models.PositiveSmallIntegerField('Priority', null=True, blank=False,
													choices=(
													(0, 0), (1, 1), (2, 2), (3, 3), (4, 4), (5, 5), (6, 6), (7, 7),
													(8, 8), (9, 9), (10, 10),),
													help_text='Enter a number between 0 and 10, with 0 being the lowest priority and 10 being the highest.')
	vtr_notes = models.TextField(null=True, blank=True, verbose_name='Notes')

	def __unicode__(self):
		return 'Review: ' + str(self.review) + ' TissueRequest: ' + str(self.tissue_request)

	def is_finished(self):
		return self.vtr_scientific_merit is not None and\
			   self.vtr_quantity is not None and\
			   self.vtr_priority is not None

	def get_request(self):
		return self.tissue_request

	def get_merit(self):
		return self.vtr_scientific_merit

	def get_quantity(self, css=False):
		if css:
			if self.vtr_quantity == "Too little":
				return 0
			elif self.vtr_quantity == "Too much":
				return 10
			else:
				return 5
		else:
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


class TissueSample(models.Model):
	tss_id = models.AutoField(primary_key=True)
	tissue_type = models.ForeignKey(TissueType, db_column='tst_type_id', related_name='tissue_sample_set', blank=False, null=False)
	monkey = models.ForeignKey(Monkey, db_column='mky_id',related_name='tissue_sample_set', blank=False, null=False)
	tss_freezer = models.CharField('Freezer Name', max_length=100, null=False, blank=True, help_text='Please enter the name of the freezer this sample is in.')
	tss_location = models.CharField('Location of Sample', max_length=100, null=False, blank=True, help_text='Please enter the location in the freezer where this sample is stored.')
	tss_details = models.TextField('Details', null=True, blank=True, help_text='Any extras details about this tissue sample.')
	tss_sample_quantity = models.FloatField('Sample Quantity', null=True, default=0)
	tss_units = models.CharField('Quantity units', choices=Units, null=False, max_length=20, default=Units[3][0])
	tss_modified = models.DateTimeField('Last Updated', auto_now_add=True, editable=False, auto_now=True)
	user = models.ForeignKey(User, verbose_name="Last Updated by", on_delete=models.SET_NULL, related_name='+', db_column='usr_usr_id', editable=False, null=True)


	def get_modified(self):
		return self.tss_modified

	def __unicode__(self):
		return "%s %s %s:%s" % (str(self.monkey), str(self.tissue_type), self.tss_freezer, self.tss_location)

	def get_location(self):
		if self.monkey.cohort.coh_upcoming:
			return "Upcoming Cohort"

		if  self.tss_freezer and self.tss_location:
			location = "%s : %s" % (self.tss_freezer, self.tss_location)
		elif  self.tss_freezer:
			location =  self.tss_freezer
		else:
			location = 'unknown'
		return location

	def get_availability(self):
		if self.monkey.cohort.coh_upcoming:
			return Availability.Available

#		# This takes SOOO long to query.  I have MonkeyBrainBlock.save() updating tss_sample_quantity
#		if 'brain' in self.tissue_type.category.cat_name.lower():
#			if MonkeyBrainBlock.objects.filter(monkey=self.monkey, tissue_types=self.tissue_type).count():
#				return Availability.In_Stock
#		elif self.tss_sample_quantity > 0: # ignore tss_sample_quantity if this is a brain tissue

		if self.tss_sample_quantity > 0:
			return Availability.In_Stock
		return Availability.Unavailable


	def get_quantity(self):
		return self.tss_sample_quantity

	def get_quantity_display(self):
		if self.monkey.cohort.coh_upcoming:
			return "Upcoming Cohort"

		samp_q = "%s %s" % (str(self.tss_sample_quantity), self.tss_units)
		if self.tss_sample_quantity is 0:
			samp_q = '0'
		if self.tss_sample_quantity is None:
			samp_q = 'unknown'
		return samp_q

	def save(self, *args, **kwargs):
		if self.monkey.mky_real_id == 0:
			self.tss_sample_quantity = 999
			self.tss_freezer = "Assay Tissue"
			self.tss_location = "Assay Tissue"
			self.tss_details = "MATRR does not track assay inventory."
		super(TissueSample, self).save(*args, **kwargs)

	def update_brain_quantity(self):
		if not 'brain' in self.tissue_type.category.cat_name.lower():
			return # ignore peripheral tissues
		brain_blocks = MonkeyBrainBlock.objects.filter(monkey=self.monkey).filter(tissue_types=self.tissue_type)
		if brain_blocks.count():
			self.tss_sample_quantity = 0.01234
		else:
			self.tss_sample_quantity = -0.01234
		self.save()

	class Meta:
		db_table = 'tss_tissue_samples'
		ordering = ['-monkey__mky_real_id', '-tissue_type__tst_tissue_name']


class Publication(models.Model):
	id = models.AutoField(primary_key=True)
	authors = models.TextField('Authors', null=True, blank=True)
	title = models.CharField('Title', max_length=200, null=True, blank=True)
	journal = models.CharField('Journal', max_length=200, null=True, blank=True)
	cohorts = models.ManyToManyField(Cohort, db_table='ptc_publications_to_cohorts',
									 verbose_name='Cohorts',
									 related_name='publication_set',
									 help_text='The cohorts involved in this publication.',
									 null=True, blank=True)
	published_year = models.CharField('Year Published', max_length=10, null=True, blank=True)
	published_month = models.CharField('Month Published', max_length=10, null=True, blank=True)
	issue = models.CharField('Issue Number', max_length=20, null=True, blank=True)
	volume = models.CharField('Volume', max_length=20, null=True, blank=True)
	pmid = models.IntegerField('PubMed ID', unique=True, null=True, blank=True)
	pmcid = models.CharField('PubMed Central ID', max_length=20, null=True, blank=True)
	isbn = models.IntegerField('ISBN', null=True, blank=True)
	abstract = models.TextField('Abstract', null=True, blank=True)
	keywords = models.TextField('Keywords', null=True, blank=True)

	pub_date = models.DateField("Publication Date", null=True, blank=True)

	def _populate_pub_date(self):
		if not self.pub_date:
			if self.published_month and self.published_year:
				date_string = "%s %s" % (self.published_month, self.published_year)
				pub_date = datetime.strptime(date_string, "%b %Y")
			elif not self.published_month and self.published_year:
				date_string = self.published_year
				pub_date = datetime.strptime(date_string, "%Y")
			else:
				pub_date = None
			self.pub_date = pub_date
			self.save()

	def publication_url(self):
		return "http://www.ncbi.nlm.nih.gov/pubmed?term=%s" % self.pmid

	def __unicode__(self):
		if self.title:
			return str(self.title.encode('ascii', 'ignore'))
		else:
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


class TissueInventoryVerification(models.Model):
	tiv_id = models.AutoField(primary_key=True)

	tissue_request = models.ForeignKey(TissueRequest, null=True, related_name='tissue_verification_set',
									   db_column='rtt_tissue_request_id', on_delete=models.SET_NULL)
	tissue_sample = models.ForeignKey(TissueSample, null=True, related_name='tissue_verification_set', db_column='tss_id')
	tissue_type = models.ForeignKey(TissueType, null=False, related_name='tissue_verification_set', db_column='tst_type_id')
	monkey = models.ForeignKey(Monkey, null=False, related_name='tissue_verification_set', db_column='mky_id')
	tiv_inventory = models.CharField('Is the tissue sample quantity sufficient to fill the indicated request?',
									 choices=InventoryStatus, null=False, max_length=100, default=InventoryStatus[0][0])
	tiv_notes = models.TextField('Verification Notes', blank=True,
								 help_text='Used to articulate database inconsistencies.')
	tiv_date_modified = models.DateTimeField(auto_now_add=True, editable=False, auto_now=True)
	tiv_date_created = models.DateTimeField(editable=False, auto_now_add=True)

	def __unicode__(self):
		return str(self.monkey) + ":" + self.tissue_type.tst_tissue_name + ': ' + self.tiv_inventory

	# Return a queryset of all TIV objects with the same monkey:tissue_type
	def get_tiv_collisions(self):
		collisions = TissueInventoryVerification.objects.exclude(tiv_id=self.tiv_id)
		collisions = collisions.filter(tissue_type=self.tissue_type)
		collisions = collisions.filter(monkey=self.monkey)
		collisions = collisions.distinct()
		return collisions

	# Reset any colliding TIVs to unverified.
	# This is used in request_post_save to invalidate inventory verifications once a tissue has been accepted,
	# forcing lab techs to re-verify the inventory for requests not yet accepted, accounting for the newly approved request.
	def invalidate_collisions(self):
		collisions = self.get_tiv_collisions()
		for tiv in collisions:
			tiv.tiv_inventory = "Unverified"
			tiv.save()

	def verify_all_TIVs(self, are_you_sure=False, are_you_double_sure=False, are_you_damn_positive=False, req_request=False):
		if settings.PRODUCTION is False or (are_you_sure and are_you_double_sure and are_you_damn_positive):
			if req_request is True:
				tivs = TissueInventoryVerification.objects.all()
			else:
				# this will error with default req_request.  You must set four separate arguments to True to verify every TIV in the db.
				tivs = TissueInventoryVerification.objects.filter(tissue_request__req_request=int(req_request))
			for tiv in tivs:
				tiv.tiv_inventory = 'Verified'
				tiv.save()


	def save(self, *args, **kwargs):
		notes = self.tiv_notes
		# This will set the tissue_sample field with several database consistency checks
		if self.tissue_sample is None:
			try:
				units = Units[3][0]
				self.tissue_sample, is_new = TissueSample.objects.get_or_create(monkey=self.monkey, tissue_type=self.tissue_type,
																				defaults={'tss_freezer': "No Previous Record",
																						  'tss_location': "No Previous Record",
																						  'tss_units': units})
				# All tissue samples should have been previously created.
				# Currently, I don't think a TIV can be created (thru the website) without a tissue sample record already existing
				if is_new:
					notes = "%s:Database Error:  There was no previous record for this monkey:tissue_type. Please notify a MATRR admin." % str(datetime.now().date())
			# There should only be 1 tissue sample for each monkey:tissue_type.
			# Possibly should make them unique-together
			except TissueSample.MultipleObjectsReturned:
				notes = "%s:Database Error:  Multiple TissueSamples exist for this monkey:tissue_type. Please notify a MATRR admin. Do not edit, changes will not be saved." % str(
					datetime.now().date())
		# tissue_sample should ALWAYS == monkey:tissue_type
		elif self.tissue_sample.monkey != self.monkey or self.tissue_sample.tissue_type != self.tissue_type:
			notes = "%s:Database Error:  This TIV has inconsistent monkey:tissue_type:tissue_sample. Please notify a MATRR admin.  Do not edit, changes will not be saved." % str(
				datetime.now().date())

		if 'Do not edit' in notes:
			# this doesnt save any other changes
			TissueInventoryVerification.objects.filter(pk=self.pk).update(tiv_notes=notes)
		else:
			self.tiv_notes = notes
			super(TissueInventoryVerification, self).save(*args, **kwargs)
			## If the tissue has been verified, but has NO tissue_request associated with it
			if self.tiv_inventory != "Unverified" and self.tissue_request is None:
				self.delete() # delete it

	class Meta:
		db_table = 'tiv_tissue_verification'
		permissions = (
		('can_verify_tissues', 'Can verify tissues'),
		)


class Metabolite(models.Model):
	met_id = models.AutoField(primary_key=True)
	met_biochemical = models.CharField(null=False, max_length=200)
	met_super_pathway = models.CharField(null=False, max_length=200)
	met_sub_pathway = models.CharField(null=False, max_length=200)
	met_comp_id = models.IntegerField()
	met_platform = models.CharField(null=False, max_length=200)

	met_ri = models.FloatField()
	met_mass = models.FloatField()

	met_cas = models.CharField(null=False, blank=True, max_length=200)
	met_kegg = models.CharField(null=False, blank=True, max_length=200, help_text='http://www.genome.jp/dbget-bin/www_bget?cpd+<value>')
	met_hmdb_id = models.CharField(null=False, blank=True, max_length=200, help_text='http://www.hmdb.ca/metabolites/<value>')

	def __unicode__(self):
		return str(self.met_biochemical)

	class Meta:
		db_table = 'met_metabolite'


class MonkeyMetabolite(models.Model):
	mmb_id = models.AutoField(primary_key=True)
	monkey = models.ForeignKey(Monkey, null=False, related_name='metabolite_set', db_column='mky_id', editable=False)
	metabolite = models.ForeignKey(Metabolite, null=False, related_name='monkey_set', db_column='met_id', editable=False)
	mmb_sample_name = models.CharField(null=False, max_length=50)
	mmb_sample_id = models.IntegerField()
	mmb_client_identifier = models.CharField("1-mky_real_id", null=False, max_length=50)
	mmb_group = models.IntegerField()
	mmb_date = models.DateTimeField(editable=False)
	mmb_treatment = models.CharField(null=False, max_length=50)
	mmb_subject_id = models.IntegerField("mky_real_id")
	mmb_group_id = models.CharField(null=False, max_length=50)
	mmb_value = models.FloatField(null=True)
	mmb_is_normalized = models.BooleanField(null=False, blank=False, default=False)

	def __unicode__(self):
		return "%s | %s | %s" % (str(self.monkey), str(self.metabolite), str(self.mmb_date))

	class Meta:
		db_table = 'mmb_monkey_metabolite'


class Protein(models.Model):
	pro_id = models.AutoField(primary_key=True)
	pro_name = models.CharField('Protein Name', null=False, blank=False, max_length=250)
	pro_abbrev = models.CharField('Protein Abbreviation', null=False, blank=False, max_length=250)
	pro_units = models.CharField('Concentration Units', choices=ProteinUnits, null=False, max_length=20)

	def __unicode__(self):
		name = self.pro_name
		if len(name) >= 32:
			name = self.pro_abbrev
		return "%s" % name

	class Meta:
		db_table = 'pro_protein'


class MonkeyProtein(models.Model):
	mpn_id = models.AutoField(primary_key=True)
	monkey = models.ForeignKey(Monkey, null=False, related_name='protein_set', db_column='mky_id', editable=False)
	protein = models.ForeignKey(Protein, null=False, related_name='monkey_set', db_column='pro_id', editable=False)
	mpn_date = models.DateTimeField("Date Collected", editable=False)
	mpn_value = models.FloatField(null=True)
	mpn_stdev = models.FloatField("Standard Deviation from Cohort mean", null=True)
	mpn_pctdev = models.FloatField("Percent Deviation from Cohort mean", null=True)

	def __unicode__(self):
		return "%s | %s | %s" % (str(self.monkey), str(self.protein), str(self.mpn_date))

	def populate_stdev(self, recalculate=False):
		if self.mpn_stdev is None or recalculate:
			cohort_proteins = MonkeyProtein.objects.filter(protein=self.protein, mpn_date=self.mpn_date, monkey__in=self.monkey.cohort.monkey_set.all().exclude(mky_id=self.monkey.pk))
			cp_values = numpy.array(cohort_proteins.values_list('mpn_value', flat=True))
			stdev = cp_values.std()
			mean = cp_values.mean()
			diff = self.mpn_value - mean
			self.mpn_stdev = diff / stdev
			self.save()

	def populate_pctdev(self, recalculate=False):
		if self.mpn_pctdev is None or recalculate:
			cohort_proteins = MonkeyProtein.objects.filter(protein=self.protein, mpn_date=self.mpn_date, monkey__in=self.monkey.cohort.monkey_set.all().exclude(mky_id=self.monkey.pk))
			cp_values = numpy.array(cohort_proteins.values_list('mpn_value', flat=True))
			mean = cp_values.mean()
			diff = self.mpn_value - mean
			self.mpn_pctdev = diff / mean * 100
			self.save()


	class Meta:
		db_table = 'mpn_monkey_protein'


class FamilyNode(models.Model):
	fmn_id = models.AutoField(primary_key=True)
	monkey = models.OneToOneField(Monkey, null=False, blank=False, related_name='genealogy')
	sire = models.ForeignKey('self', null=True, blank=True, related_name='+')
	dam = models.ForeignKey('self', null=True, blank=True, related_name='+')
	kin = models.ManyToManyField('self', symmetrical=False, null=True, blank=True, through='FamilyRelationship', related_name='+')

	def create_parent_relationships(self):
		if self.sire:
			fathers_son = FamilyRelationship.objects.get_or_create(me=self, relative=self.sire, fmr_type=FamilyRelationship.RELATIONSHIP.Offspring)[0]
			sons_father = FamilyRelationship.objects.get_or_create(relative=self, me=self.sire, fmr_type=FamilyRelationship.RELATIONSHIP.Parent)[0]
		if self.dam:
			mothers_son = FamilyRelationship.objects.get_or_create(me=self, relative=self.dam, fmr_type=FamilyRelationship.RELATIONSHIP.Offspring)[0]
			sons_mother = FamilyRelationship.objects.get_or_create(relative=self, me=self.dam, fmr_type=FamilyRelationship.RELATIONSHIP.Parent)[0]
		return

	def __unicode__(self):
		return "FMN:%s" % str(self.monkey)

	class Meta:
		permissions = ([
			('genealogy_tools', 'Can modify monkey genealogy'),
			('genealogy', 'Can view monkey genealogy'),
		])
		db_table = 'fmn_family_node'


class FamilyRelationship(models.Model):
	RELATIONSHIP = Enumeration([('P', 'Parent', 'Parent'),('O', 'Offspring', 'Offspring')])
	fmr_id = models.AutoField(primary_key=True)
	me = models.ForeignKey(FamilyNode, related_name='my_relations', null=False, blank=False)
	relative = models.ForeignKey(FamilyNode, related_name='relations_with_me', null=False, blank=False)
	fmr_type = models.CharField('Relationship Type', max_length=2, choices=RELATIONSHIP)
	fmr_coeff = models.FloatField('Relationship Coefficient', blank=False, null=True, default=None)
	#  There are going to be 2 records in this table for each relationship, source <-> target.   The type of relationship gets tricky to define.
	#  (Grand)Parents are easy to define, but aunts/uncles/cousins/halfcousins/halfsiblings and it continues to get worse.
	#  Plotting _a_ monkey's lineage should be easy.  Plotting two monkey's relationship to each other is gonna be nuts.

	def reverse(self):
		return FamilyRelationship.objects.get(relative=self.me, me=self.relative)

	def __unicode__(self):
		return "Relation: %s is %s of %s" % (str(self.me), self.get_fmr_type_display(), str(self.relative))

	class Meta:
		db_table = 'fmr_family_relationship'


class MonkeyHormone(models.Model):
	mhm_id = models.AutoField(primary_key=True)
	monkey = models.ForeignKey(Monkey, null=False, related_name='hormone_records', db_column='mky_id', editable=False)
	mhm_date = models.DateTimeField("Date Collected", editable=False, null=True, blank=False)
	mhm_cort = models.FloatField("Cortisol", null=True, blank=True)
	mhm_acth = models.FloatField("ACTH", null=True, blank=True)
	mhm_t = models.FloatField("Testosterone", null=True, blank=True)
	mhm_doc = models.FloatField("Deoxycorticosterone", null=True, blank=True)
	mhm_ald = models.FloatField("Aldosterone", null=True, blank=True)
	mhm_dheas = models.FloatField("DHEAS", null=True, blank=True)

	def __unicode__(self):
		return "%s | %s" % (str(self.monkey), str(self.mhm_date))

	class Meta:
		db_table = 'mhm_monkey_hormone'


class MonkeyBEC(models.Model):
	bec_id = models.AutoField(primary_key=True)
	monkey = models.ForeignKey(Monkey, null=False, related_name='bec_records', db_column='mky_id', editable=False)
	mtd = models.OneToOneField(MonkeyToDrinkingExperiment, null=True, related_name='bec_record', editable=False, on_delete=models.SET_NULL)
	bec_collect_date = models.DateTimeField("Date Collected", editable=False, null=True, blank=False)
	bec_run_date = models.DateTimeField("Date Run", editable=False, null=True, blank=False)
	bec_exper = models.CharField('Experiment Type', max_length=20, null=True, blank=True)
	bec_exper_day = models.IntegerField('Experiment Day', editable=False, null=True, blank=False)
	bec_session_start = models.TimeField("Session Start", editable=False, null=True, blank=False)
	bec_sample = models.TimeField("Session Start", editable=False, null=True, blank=False)
	bec_weight = models.FloatField("Monkey Weight (week)", null=True, blank=True)
	bec_vol_etoh = models.FloatField("Etoh at sample time, ml", null=True, blank=True)
	bec_gkg_etoh = models.FloatField("Etoh at sample time, g/kg", null=True, blank=True)
	bec_daily_gkg_etoh = models.FloatField("Total Etoh, g/kg", null=True, blank=True)
	bec_mg_pct = models.FloatField("Blood Ethanol Conc., mg %", null=False, blank=False)

	bec_pct_intake = models.FloatField("Sample Volume / Total Intake", null=True, blank=True)


	def __unicode__(self):
		return "%s | %s | %s" % (str(self.monkey), str(self.bec_collect_date), str(self.bec_mg_pct))

	def populate_fields(self, repopulate=True):
		save = False
		if not self.mtd or repopulate:
			mtd = MonkeyToDrinkingExperiment.objects.filter(monkey=self.monkey, drinking_experiment__dex_date=self.bec_collect_date)
			if mtd.count() is 1:
				self.mtd = mtd[0]
				save = True
		if not self.bec_pct_intake or repopulate:
			if self.bec_daily_gkg_etoh and self.bec_daily_gkg_etoh:
				self.bec_pct_intake = float(self.bec_gkg_etoh) / self.bec_daily_gkg_etoh
			else:
				self.bec_pct_intake = 0
			save = True
		if save:
			self.save()

	class Meta:
		db_table = 'bec_monkey_bec'
		permissions = (
		[('view_bec_data', 'Can view BEC data'),
		])


class CohortMetaData(models.Model):
	# Origionally this object was named CohortBEC, shortname cbc
	# Table grew into more than BEC, but I'm leaving the shortname of this table cbc.
	# I'm not naming an object cmd, the very established shortname for 'command'
	# -jf 29Nov2012
	cbc_id = models.AutoField(primary_key=True)
	cohort = models.OneToOneField(Cohort, null=False, blank=False, related_name='cbc', editable=False)

	cbc_bec_mg_pct_min = models.FloatField("Minimum BEC, mg %", null=True, blank=False)
	cbc_bec_mg_pct_max = models.FloatField("Maximum BEC, mg %", null=True, blank=False)
	cbc_bec_mg_pct_avg = models.FloatField("Average BEC, mg %", null=True, blank=False)

	cbc_bec_etoh_min = models.FloatField("Minimum Etoh Intake at BEC Blood Sample, in ml", null=True, blank=False)
	cbc_bec_etoh_max = models.FloatField("Maximum Etoh Intake at BEC Blood Sample, in ml", null=True, blank=False)
	cbc_bec_etoh_avg = models.FloatField("Average Etoh Intake at BEC Blood Sample, in ml", null=True, blank=False)

	cbc_bec_gkg_etoh_min = models.FloatField("Minimum Etoh Intake at BEC Blood Sample, in g/kg", null=True, blank=False)
	cbc_bec_gkg_etoh_max = models.FloatField("Maximum Etoh Intake at BEC Blood Sample, in g/kg", null=True, blank=False)
	cbc_bec_gkg_etoh_avg = models.FloatField("Average Etoh Intake at BEC Blood Sample, in g/kg", null=True, blank=False)

	cbc_bec_pct_intake_min = models.FloatField("Minimum Percentage Intake at BEC Blood Sample", null=True, blank=False)
	cbc_bec_pct_intake_max = models.FloatField("Maximum Percentage Intake at BEC Blood Sample", null=True, blank=False)
	cbc_bec_pct_intake_avg = models.FloatField("Average Percentage Intake at BEC Blood Sample", null=True, blank=False)

	cbc_mtd_etoh_g_kg_min = models.FloatField('Minimum Etoh intake per day, in g/kg', null=True, blank=False)
	cbc_mtd_etoh_g_kg_max = models.FloatField('Maximum Etoh intake per day, in g/kg', null=True, blank=False)
	cbc_mtd_etoh_g_kg_avg = models.FloatField('Average Etoh intake per day, in g/kg', null=True, blank=False)

	cbc_mtd_etoh_bout_min = models.FloatField('Minimum Etoh Bouts per day', null=True, blank=True)
	cbc_mtd_etoh_bout_max = models.FloatField('Maximum Etoh Bouts per day', null=True, blank=True)
	cbc_mtd_etoh_bout_avg = models.FloatField('Average Etoh Bouts per day', null=True, blank=True)

	cbc_mtd_etoh_drink_bout_min = models.FloatField('Minimum Etoh Bouts per bout per day', null=True, blank=True)
	cbc_mtd_etoh_drink_bout_max = models.FloatField('Maximum Etoh Bouts per bout per day', null=True, blank=True)
	cbc_mtd_etoh_drink_bout_avg = models.FloatField('Average Etoh Bouts per bout per day', null=True, blank=True)

	cbc_mtd_pct_max_bout_vol_total_etoh_min = models.FloatField('Minimum Max Bout Volume as % of Total Etoh per day', null=True, blank=True)
	cbc_mtd_pct_max_bout_vol_total_etoh_max = models.FloatField('Maximum Max Bout Volume as % of Total Etoh per day', null=True, blank=True)
	cbc_mtd_pct_max_bout_vol_total_etoh_avg = models.FloatField('Average Max Bout Volume as % of Total Etoh per day', null=True, blank=True)

	cbc_mtd_max_bout_length_min = models.FloatField('Minimum Max Bout Length per day', null=True, blank=True)
	cbc_mtd_max_bout_length_max = models.FloatField('Maximum Max Bout Length per day', null=True, blank=True)
	cbc_mtd_max_bout_length_avg = models.FloatField('Average Max Bout Length per day', null=True, blank=True)

	cbc_mtd_max_bout_vol_min = models.FloatField('Minimum Max Bout Volume per day', null=True, blank=True)
	cbc_mtd_max_bout_vol_max = models.FloatField('Maximum Max Bout Volume per day', null=True, blank=True)
	cbc_mtd_max_bout_vol_avg = models.FloatField('Average Max Bout Volume per day', null=True, blank=True)

	cbc_mtd_vol_1st_bout_min = models.FloatField('Minimum Vol. 1st Bout per day', null=True, blank=True)
	cbc_mtd_vol_1st_bout_max = models.FloatField('Maximum Vol. 1st Bout per day', null=True, blank=True)
	cbc_mtd_vol_1st_bout_avg = models.FloatField('Average Vol. 1st Bout per day', null=True, blank=True)

	cbc_mtd_pct_etoh_in_1st_bout_min = models.FloatField('Minimum % Etoh in First Bout per day', null=True, blank=True)
	cbc_mtd_pct_etoh_in_1st_bout_max = models.FloatField('Maximum % Etoh in First Bout per day', null=True, blank=True)
	cbc_mtd_pct_etoh_in_1st_bout_avg = models.FloatField('Average % Etoh in First Bout per day', null=True, blank=True)

	cbc_mtd_etoh_intake_min = models.FloatField('Minimum Etoh Intake', null=True, blank=True)
	cbc_mtd_etoh_intake_max = models.FloatField('Maximum Etoh Intake', null=True, blank=True)
	cbc_mtd_etoh_intake_avg = models.FloatField('Average Etoh Intake', null=True, blank=True)

	cbc_mtd_etoh_bout_min = models.FloatField('Minimum EtOH Bout', null=True, blank=True)
	cbc_mtd_etoh_bout_max = models.FloatField('Maximum EtOH Bout', null=True, blank=True)
	cbc_mtd_etoh_bout_avg = models.FloatField('Average EtOH Bout', null=True, blank=True)

	cbc_mtd_etoh_drink_bout_min = models.FloatField('Minimum EtOH Drink/Bout', null=True, blank=True)
	cbc_mtd_etoh_drink_bout_max = models.FloatField('Maximum EtOH Drink/Bout', null=True, blank=True)
	cbc_mtd_etoh_drink_bout_avg = models.FloatField('Average EtOH Drink/Bout', null=True, blank=True)

	cbc_mtd_etoh_mean_drink_vol_min = models.FloatField('Minimum EtOH Mean Drink Vol', null=True, blank=True)
	cbc_mtd_etoh_mean_drink_vol_max = models.FloatField('Maximum EtOH Mean Drink Vol', null=True, blank=True)
	cbc_mtd_etoh_mean_drink_vol_avg = models.FloatField('Average EtOH Mean Drink Vol', null=True, blank=True)

	cbc_mtd_etoh_mean_bout_vol_min = models.FloatField('Minimum EtOH Mean Bout Vol', null=True, blank=True)
	cbc_mtd_etoh_mean_bout_vol_max = models.FloatField('Maximum EtOH Mean Bout Vol', null=True, blank=True)
	cbc_mtd_etoh_mean_bout_vol_avg = models.FloatField('Average EtOH Mean Bout Vol', null=True, blank=True)

	cbc_total_drinks_min = models.FloatField('Minimum total drinks per day', null=True, blank=True) # this field is fuzzy.  It's a guestimate derived from an average
	cbc_total_drinks_max = models.FloatField('Maximum total drinks per day', null=True, blank=True) # this field is fuzzy.  It's a guestimate derived from an average
	cbc_total_drinks_avg = models.FloatField('Average total drinks per day', null=True, blank=True) # this field is fuzzy.  It's a guestimate derived from an average

	cbc_ebt_volume_min = models.FloatField('Minimum Etoh Bout volume per day', null=True, blank=True)
	cbc_ebt_volume_max = models.FloatField('Maximum Etoh Bout volume per day', null=True, blank=True)
	cbc_ebt_volume_avg = models.FloatField('Average Etoh Bout volume per day', null=True, blank=True)


	def __unicode__(self):
		return "%s metadata" % str(self.cohort)

	def populate_self(self):
		becs = MonkeyBEC.objects.filter(monkey__cohort=self.cohort)
		data = becs.aggregate(Min('bec_mg_pct'), Max('bec_mg_pct'), Avg('bec_mg_pct'))
		self.cbc_bec_mg_pct_min = data['bec_mg_pct__min']
		self.cbc_bec_mg_pct_max = data['bec_mg_pct__max']
		self.cbc_bec_mg_pct_avg = data['bec_mg_pct__avg']

		data = becs.aggregate(Min('bec_vol_etoh'), Max('bec_vol_etoh'), Avg('bec_vol_etoh'))
		self.cbc_bec_etoh_min = data['bec_vol_etoh__min']
		self.cbc_bec_etoh_max = data['bec_vol_etoh__max']
		self.cbc_bec_etoh_avg = data['bec_vol_etoh__avg']

		data = becs.aggregate(Min('bec_gkg_etoh'), Max('bec_gkg_etoh'), Avg('bec_gkg_etoh'))
		self.cbc_bec_gkg_etoh_min = data['bec_gkg_etoh__min']
		self.cbc_bec_gkg_etoh_max = data['bec_gkg_etoh__max']
		self.cbc_bec_gkg_etoh_avg = data['bec_gkg_etoh__avg']

		data = becs.aggregate(Min('bec_pct_intake'), Max('bec_pct_intake'), Avg('bec_pct_intake'))
		self.cbc_bec_pct_intake_min = data['bec_pct_intake__min']
		self.cbc_bec_pct_intake_max = data['bec_pct_intake__max']
		self.cbc_bec_pct_intake_avg = data['bec_pct_intake__avg']

		mtds = MonkeyToDrinkingExperiment.objects.filter(monkey__cohort=self.cohort)
		data = mtds.aggregate(Min('mtd_etoh_g_kg'), Max('mtd_etoh_g_kg'), Avg('mtd_etoh_g_kg'))
		self.cbc_mtd_etoh_g_kg_min = data['mtd_etoh_g_kg__min']
		self.cbc_mtd_etoh_g_kg_max = data['mtd_etoh_g_kg__max']
		self.cbc_mtd_etoh_g_kg_avg = data['mtd_etoh_g_kg__avg']

		data = mtds.aggregate(Min('mtd_etoh_bout'), Max('mtd_etoh_bout'), Avg('mtd_etoh_bout'))
		self.cbc_mtd_etoh_bout_min = data['mtd_etoh_bout__min']
		self.cbc_mtd_etoh_bout_max = data['mtd_etoh_bout__max']
		self.cbc_mtd_etoh_bout_avg = data['mtd_etoh_bout__avg']

		data = mtds.aggregate(Min('mtd_etoh_drink_bout'), Max('mtd_etoh_drink_bout'), Avg('mtd_etoh_drink_bout'))
		self.cbc_mtd_etoh_drink_bout_min = data['mtd_etoh_drink_bout__min']
		self.cbc_mtd_etoh_drink_bout_max = data['mtd_etoh_drink_bout__max']
		self.cbc_mtd_etoh_drink_bout_avg = data['mtd_etoh_drink_bout__avg']

		data = mtds.aggregate(Min('mtd_pct_max_bout_vol_total_etoh'), Max('mtd_pct_max_bout_vol_total_etoh'), Avg('mtd_pct_max_bout_vol_total_etoh'))
		self.cbc_mtd_pct_max_bout_vol_total_etoh_min = data['mtd_pct_max_bout_vol_total_etoh__min']
		self.cbc_mtd_pct_max_bout_vol_total_etoh_max = data['mtd_pct_max_bout_vol_total_etoh__max']
		self.cbc_mtd_pct_max_bout_vol_total_etoh_avg = data['mtd_pct_max_bout_vol_total_etoh__avg']

		data = mtds.aggregate(Min('mtd_max_bout_length'), Max('mtd_max_bout_length'), Avg('mtd_max_bout_length'))
		self.cbc_mtd_max_bout_length_min = data['mtd_max_bout_length__min']
		self.cbc_mtd_max_bout_length_max = data['mtd_max_bout_length__max']
		self.cbc_mtd_max_bout_length_avg = data['mtd_max_bout_length__avg']

		data = mtds.aggregate(Min('mtd_max_bout_vol'), Max('mtd_max_bout_vol'), Avg('mtd_max_bout_vol'))
		self.cbc_mtd_max_bout_vol_min = data['mtd_max_bout_vol__min']
		self.cbc_mtd_max_bout_vol_max = data['mtd_max_bout_vol__max']
		self.cbc_mtd_max_bout_vol_avg = data['mtd_max_bout_vol__avg']

		data = mtds.aggregate(Min('mtd_vol_1st_bout'), Max('mtd_vol_1st_bout'), Avg('mtd_vol_1st_bout'))
		self.cbc_mtd_vol_1st_bout_min = data['mtd_vol_1st_bout__min']
		self.cbc_mtd_vol_1st_bout_max = data['mtd_vol_1st_bout__max']
		self.cbc_mtd_vol_1st_bout_avg = data['mtd_vol_1st_bout__avg']

		data = mtds.aggregate(Min('mtd_pct_etoh_in_1st_bout'), Max('mtd_pct_etoh_in_1st_bout'), Avg('mtd_pct_etoh_in_1st_bout'))
		self.cbc_mtd_pct_etoh_in_1st_bout_min = data['mtd_pct_etoh_in_1st_bout__min']
		self.cbc_mtd_pct_etoh_in_1st_bout_max = data['mtd_pct_etoh_in_1st_bout__max']
		self.cbc_mtd_pct_etoh_in_1st_bout_avg = data['mtd_pct_etoh_in_1st_bout__avg']

		data = mtds.aggregate(Min('mtd_etoh_intake'), Max('mtd_etoh_intake'), Avg('mtd_etoh_intake'))
		self.cbc_mtd_etoh_intake_min = data['mtd_etoh_intake__min']
		self.cbc_mtd_etoh_intake_max = data['mtd_etoh_intake__max']
		self.cbc_mtd_etoh_intake_avg = data['mtd_etoh_intake__avg']

		data = mtds.aggregate(Min('mtd_etoh_bout'), Max('mtd_etoh_bout'), Avg('mtd_etoh_bout'))
		self.cbc_mtd_etoh_bout_min = data['mtd_etoh_bout__min']
		self.cbc_mtd_etoh_bout_max = data['mtd_etoh_bout__max']
		self.cbc_mtd_etoh_bout_avg = data['mtd_etoh_bout__avg']

		data = mtds.aggregate(Min('mtd_etoh_drink_bout'), Max('mtd_etoh_drink_bout'), Avg('mtd_etoh_drink_bout'))
		self.cbc_mtd_etoh_drink_bout_min = data['mtd_etoh_drink_bout__min']
		self.cbc_mtd_etoh_drink_bout_max = data['mtd_etoh_drink_bout__max']
		self.cbc_mtd_etoh_drink_bout_avg = data['mtd_etoh_drink_bout__avg']

		data = mtds.aggregate(Min('mtd_etoh_mean_drink_vol'), Max('mtd_etoh_mean_drink_vol'), Avg('mtd_etoh_mean_drink_vol'))
		self.cbc_mtd_etoh_mean_drink_vol_min = data['mtd_etoh_mean_drink_vol__min']
		self.cbc_mtd_etoh_mean_drink_vol_max = data['mtd_etoh_mean_drink_vol__max']
		self.cbc_mtd_etoh_mean_drink_vol_avg = data['mtd_etoh_mean_drink_vol__avg']

		data = mtds.aggregate(Min('mtd_etoh_mean_bout_vol'), Max('mtd_etoh_mean_bout_vol'), Avg('mtd_etoh_mean_bout_vol'))
		self.cbc_mtd_etoh_mean_bout_vol_min = data['mtd_etoh_mean_bout_vol__min']
		self.cbc_mtd_etoh_mean_bout_vol_max = data['mtd_etoh_mean_bout_vol__max']
		self.cbc_mtd_etoh_mean_bout_vol_avg = data['mtd_etoh_mean_bout_vol__avg']

		_data = mtds.values_list('mtd_etoh_drink_bout', 'mtd_etoh_bout')
		data = numpy.array([d[0]*d[1] if all(d) else 0 for d in _data])
		if data.any():
			self.cbc_total_drinks_min = data.min()
			self.cbc_total_drinks_max = data.max()
			self.cbc_total_drinks_avg = data.mean()

		bouts = ExperimentBout.objects.filter(mtd__monkey__cohort=self.cohort)
		data = bouts.aggregate(Min('ebt_volume'), Max('ebt_volume'), Avg('ebt_volume'))
		self.cbc_ebt_volume_min = data['ebt_volume__min']
		self.cbc_ebt_volume_max = data['ebt_volume__max']
		self.cbc_ebt_volume_avg = data['ebt_volume__avg']

		self.save()

	class Meta:
		db_table = 'cbc_cohort_metadata'


class RNARecord(models.Model):
	rna_id = models.AutoField(primary_key=True)
	tissue_type = models.ForeignKey(TissueType, db_column='tst_type_id', related_name='rna_set', blank=False, null=False)
	cohort = models.ForeignKey(Cohort, db_column='coh_cohort_id', related_name='rna_set', editable=False, blank=False, null=False)
	user = models.ForeignKey(User, verbose_name="Last Updated by", on_delete=models.SET(get_sentinel_user), related_name='rna_set', editable=False, null=False)
	monkey = models.ForeignKey(Monkey, db_column='mky_id', related_name='rna_set', blank=True, null=True)

	rna_modified = models.DateTimeField('Last Updated', auto_now_add=True, editable=False, auto_now=True)
	rna_min = models.IntegerField("Minimum yield (in micrograms)", "Min Yield", blank=False, null=False)
	rna_max = models.IntegerField("Maximum yield (in micrograms)", "Max Yield", blank=False, null=False)

	def __unicode__(self):
		return "%s | %s | %.2f-%.2f" % (str(self.cohort), str(self.tissue_type), self.rna_min, self.rna_max)

	def clean(self):
		# Don't allow user to select a monkey not in the (previously) chosen cohort.
		if self.monkey and self.cohort != self.monkey.cohort:
			raise Exception('The selected monkey is not part of the chosen cohort')
		# And invert the min/max if they're not correctly labeled
		if self.rna_min > self.rna_max:
			min = self.rna_max
			self.rna_max = self.rna_min
			self.rna_min = min

	class Meta:
		db_table = 'rna_rnarecord'
		ordering = ['cohort__coh_cohort_name', 'tissue_type', 'monkey']
		permissions = ([
			('rna_submit', 	'Can submit RNA yields'),
			('rna_display', 	'Can view RNA yields'),
		])


class MonkeyBrainBlock(models.Model):
	mbb_id = models.AutoField(primary_key=True)
	monkey = models.ForeignKey(Monkey, null=False, blank=False, related_name='brainblock_set')
	tissue_types = models.ManyToManyField(TissueType, symmetrical=False, null=True, blank=True, related_name='brainblock_set')
	mbb_block_name = models.CharField(max_length=20)
	mbb_hemisphere = models.CharField('Hemisphere', max_length=5, choices=(('L', 'Left'), ('R', 'Right')))
	brain_image = models.ForeignKey(MonkeyImage, null=True, blank=True, related_name='brainblock_set', on_delete=models.SET_NULL)


	def __unicode__(self):
		return "Brain %s for monkey %d" % (self.mbb_block_name, self.monkey.pk)

	def save(self, *args, **kwargs):
		super(MonkeyBrainBlock, self).save(*args, **kwargs)
		if self.tissue_types.exclude(category__cat_name__icontains='brain').count():
			raise Exception("Cannot add non-brain tissue type to MonkeyBrainBlock.tissue_types")
		self.update_tss_sample_quantity()

	def update_tss_sample_quantity(self):
		for tst in TissueType.objects.filter(category__cat_name__icontains='brain'):
			tss = TissueSample.objects.get(monkey=self.monkey, tissue_type=tst)
			tss.update_brain_quantity()

	def image_url(self):
		return self.brain_image.image.url

	def fragment_url(self):
		return self.brain_image.html_fragment.url

	def assign_tissues(self, iterable):
		self.tissue_types.clear()
		self.tissue_types.add(*iterable)
		self.save()

	class Meta:
		permissions = ([
			('brainblock_update', 	'Can update brain inventory'),
		])
		db_table = 'mbb_monkey_brain_block'


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
	if req_request._previous_status is None or\
	   req_request.req_status == req_request._previous_status:
		# if there was no change, don't do anything
		return

	current_status = req_request.req_status
	previous_status = req_request._previous_status
	tissue_requests = TissueRequest.objects.filter(req_request=req_request.req_request_id)

	# For Submitted Requests
	if previous_status in (RequestStatus.Cart, RequestStatus.Revised, RequestStatus.Duplicated)\
	and current_status == RequestStatus.Submitted:
		from matrr.emails import send_new_request_info
		# Send email notification the request was submitted
		send_new_request_info(req_request)
		# start by finding all members of the group 'Committee'
		#committee_group = Group.objects.get(name='Committee')
		#committee_members = committee_group.user_set.all()
		#		rather use users that has permission to modify reviews
		committee_members = Account.objects.users_with_perm('change_review')

		# for each committee member, create a new review for the request
		for user in committee_members:
			review = Review(req_request=req_request, user=user)
			review.save()
			# create a new TissueRequestReview for each TissueRequest
			for tissue_request in tissue_requests:
				TissueRequestReview(review=review, tissue_request=tissue_request).save()

		# If any verifications exist for this Request, delete them.  There shouldn't be any.
		TissueInventoryVerification.objects.filter(tissue_request__req_request=req_request).delete()
		# Create new TIVs.
		for tissue_request in tissue_requests:
			for monkey in tissue_request.monkeys.all():
				tv = TissueInventoryVerification.objects.create(tissue_type=tissue_request.tissue_type,
																monkey=monkey,
																tissue_request=tissue_request)
				tv.save()

		#  Kathy wants an email sent to Jim whenever someone requests a Hippocampus
		hippocampus = TissueType.objects.get(tst_tissue_name='Hippocampus').pk
		tissues = req_request.tissue_request_set.all().values_list('tissue_type', flat=True)
		if hippocampus in tissues:
			from matrr.emails import send_jim_hippocampus_notification
			send_jim_hippocampus_notification(req_request)
	# For Accepted and Partially accepted Requests
	if previous_status == RequestStatus.Submitted\
	and (current_status == RequestStatus.Accepted or current_status == RequestStatus.Partially):
		for tissue_request in tissue_requests:
			tivs = TissueInventoryVerification.objects.filter(tissue_request=tissue_request)
			for tiv in tivs:
				# Reset any colliding TIVs of accepted monkeys to 'Unverified'
				# This makes a lab tech re-verify the freezer for other submitted orders
				if tiv.monkey in tissue_request.accepted_monkeys.all():
					tiv.invalidate_collisions()
				tiv.delete()

	# For Rejected Requests
	if previous_status == RequestStatus.Submitted\
	and current_status == RequestStatus.Rejected:
		for tissue_request in tissue_requests:
			# Delete the rejected tissues' TIVs
			TissueInventoryVerification.objects.filter(tissue_request=tissue_request).delete()

	# For Shipped Requests
	if (previous_status == RequestStatus.Accepted or previous_status == RequestStatus.Partially)\
	and current_status == RequestStatus.Shipped:
		# Create new TIVs to update MATRR inventory after a tissue has shipped.
		for tissue_request in tissue_requests:
			for monkey in tissue_request.accepted_monkeys.all().exclude(mky_real_id=0): # dont create tivs for assay monkeys after shipment
				tv = TissueInventoryVerification.objects.create(tissue_type=tissue_request.tissue_type,
																monkey=monkey,
																tissue_request=None)
				tv.save()

	req_request._previous_status = None

# This is a method to check to see if a user_id exists that does not have
# an account attached to it.
@receiver(post_save, sender=User)
def user_post_save(**kwargs):
	#check to see if user exists in accounts relation
	user = kwargs['instance']
	if not Account.objects.filter(user=user).count():
		account = Account(user=user)
		account.save()

# This is a method to check to see if a cohort exists that does not have
# an CohortMetaData attached to it.
@receiver(post_save, sender=Cohort)
def cohort_post_save(**kwargs):
	#check to see if user exists in accounts relation
	cohort = kwargs['instance']
	if not CohortMetaData.objects.filter(cohort=cohort).count():
		cbc = CohortMetaData(cohort=cohort)
		cbc.populate_self()

# This will delete MATRRImage's FileField's files from media before deleting the database entry.
# Helps keep the media folder pretty.
@receiver(pre_delete, sender=MonkeyImage)
def monkeyimage_pre_delete(**kwargs):
	mig = kwargs['instance']
	if mig.image and os.path.exists(mig.image.path):
		os.remove(mig.image.path)
	if mig.thumbnail and os.path.exists(mig.thumbnail.path):
		os.remove(mig.thumbnail.path)
	if mig.html_fragment and os.path.exists(mig.html_fragment.path):
		os.remove(mig.html_fragment.path)

# This will delete MATRRImage's FileField's files from media before deleting the database entry.
# Helps keep the media folder pretty.
@receiver(pre_delete, sender=MonkeyProteinImage)
def monkeyproteinimage_pre_delete(**kwargs):
	mpi = kwargs['instance']
	if mpi.image and os.path.exists(mpi.image.path):
		os.remove(mpi.image.path)
	if mpi.thumbnail and os.path.exists(mpi.thumbnail.path):
		os.remove(mpi.thumbnail.path)
	if mpi.html_fragment and os.path.exists(mpi.html_fragment.path):
		os.remove(mpi.html_fragment.path)

# This will delete MATRRImage's FileField's files from media before deleting the database entry.
# Helps keep the media folder pretty.
@receiver(pre_delete, sender=CohortImage)
def cohortimage_pre_delete(**kwargs):
	cig = kwargs['instance']
	if cig.image and os.path.exists(cig.image.path):
		os.remove(cig.image.path)
	if cig.thumbnail and os.path.exists(cig.thumbnail.path):
		os.remove(cig.thumbnail.path)
	if cig.html_fragment and os.path.exists(cig.html_fragment.path):
		os.remove(cig.html_fragment.path)

@receiver(pre_delete, sender=DataFile)
def datafile_pre_delete(**kwargs):
	dat = kwargs['instance']
	if dat.dat_data_file and os.path.exists(dat.dat_data_file.path):
		os.remove(dat.dat_data_file.path)

@receiver(post_save, sender=TissueInventoryVerification)
def tiv_post_save(**kwargs):
	# see if all the TIVs for the request have been verified
	tiv = kwargs['instance']
	if tiv.tiv_inventory != "Unverified":
		if not tiv.tissue_request is None:
			req_request = tiv.tissue_request.req_request
			verification_status = req_request.get_inventory_verification_status()
			if verification_status == VerificationStatus.Complete:
				from matrr.emails import send_verification_complete_notification
				send_verification_complete_notification(req_request)

# This is a method to check to see if the rud_data_available boolean has changed to True
# If True, it will email matrr_admin that there is some data ready to be uploaded.
@receiver(pre_save, sender=ResearchUpdate)
def rud_pre_save(**kwargs):
	#check to see if user exists in accounts relation
	new_rud = kwargs['instance']
	try:
		old_rud = ResearchUpdate.objects.get(pk=new_rud.pk)
		old_data = old_rud.rud_data_available
	except ResearchUpdate.DoesNotExist:
		old_data = False
		
	if new_rud.rud_data_available and not old_data:
		from matrr import emails
		emails.send_rud_data_available_email(new_rud)
