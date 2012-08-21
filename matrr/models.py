#encoding=utf-8
import Image
import os, ast
from django.core.files.base import File
from django.core.mail.message import EmailMessage
from django.db import models
from django.db.models import Q
from django.contrib.auth.models import User, Group, Permission
from django.db.models.query import QuerySet
from django.db.models.signals import post_save, pre_delete
from django.core.urlresolvers import reverse
from django.dispatch import receiver
from datetime import datetime
from string import lower, replace
from django.core.validators import MaxValueValidator, MinValueValidator
from django.core.exceptions import ValidationError
import numpy
from matrr.process_latex import process_latex
import settings

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


# These are the method names which ONLY VIP members can _see_
VIP_IMAGES_LIST = (
'monkey_bouts_drinks',
'monkey_bouts_drinks_intraday',
'monkey_first_max_bout',
'monkey_bouts_vol',
'monkey_errorbox_etoh',
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
	SEX_CHOICES = (
	('M', 'Male'),
	('F', 'Female'),
	)
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
	mky_birthdate = models.DateField('Date of Birth', blank=True, null=True,
									 max_length=20,
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
	mky_study_complete = models.BooleanField('Complete Study Performed', null=False,
											 default=False,
											 help_text='Did this monkey complete all stages of the experiment?')
	mky_stress_model = models.CharField('Stress Model', null=True, blank=True,
										max_length=30,
										help_text='This should indicate the grouping of the monkey if it was in a cohort that also tested stress models. (ex. MR, NR, HC, LC) ')
	mky_age_at_necropsy = models.CharField('Age at Necropsy', max_length=100, null=True, blank=True)
	mky_notes = models.CharField('Monkey Notes', null=True, blank=True, max_length=1000, )

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

	class Meta:
		db_table = 'mky_monkeys'
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

	def save(self, *args, **kwargs):
		super(Account, self).save(*args, **kwargs)


	class Meta:
		db_table = 'act_account'
		permissions = ([
			('view_other_accounts', 'Can view accounts of other users'),
			('view_etoh_data', 'Can view ethanol data'),
			('bcc_request_email', 'Will receive BCC of processed request emails'),
			('po_manifest_email', 'Will receive Purchase Order shipping manifest email'),
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


class MonkeyToDrinkingExperiment(models.Model):
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
	mtd_pct_max_bout_vol_total_etoh = models.FloatField('Max Bout Volume as % of Total Etoh', blank=True, null=True,
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
	eev_source_row_number = models.PositiveIntegerField('Source file row number', blank=False, null=False)
	mtd = models.ForeignKey(MonkeyToDrinkingExperiment, null=False, db_column='mtd_id', related_name='events_set')
	eev_occurred = models.DateTimeField('Event occurred', blank=False, null=False)
	eev_dose = models.FloatField('Dose', blank=False, null=False)
	eev_panel = models.PositiveIntegerField('Panel', null=False, blank=False)
	eev_fixed_time = models.PositiveIntegerField('Fixed time [s]', blank=False, null=False)
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

	class Meta:
		db_table = 'eev_experiment_events'


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

	thumbnail_size = (240, 240)

	def _construct_filefields(self, mpl_figure, data_map, *args, **kwargs):
		# export the image and thumbnail to a temp folder and save them to the self.ImageFields
		if mpl_figure:
			image, thumbnail, svg_image_path = self._draw_image(mpl_figure)
			self.image = File(open(image, 'r'))
			self.thumbnail = File(open(thumbnail, 'r'))
			self.svg_image = File(open(svg_image_path, 'r'))
			# generate the html fragment for the image and save it
			if data_map != "NO MAP":
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

	def _build_html_fragment(self, data_map, add_footer=True):
		from django.template.context import Context
		from django.template.loader import get_template

		fragment_path = '/tmp/%s.html' % str(self)

		t = get_template('html_fragments/%s.html' % self.method) # templates will be named identical to the plotting method
		c = Context({'map': data_map, 'image': self, 'bigWidth': self.image.width * 1.1, 'bigHeight': self.image.height * 1.1})
#		print self.__class__.name
		foot_t = get_template('html_fragments/fragment_foot.html')
		foot_c = Context({'html_fragment': str(self).replace(" ", "_").replace('(', "").replace(")",""),
						 'class': self.__class__.__name__, 'imageID': self.pk})
		
		html_fragment = open(fragment_path, 'w+')
		html_fragment.write(str(t.render(c)))
		if add_footer:
			html_fragment.write(str(foot_t.render(foot_c)))
		html_fragment.flush()
		html_fragment.close()
		return fragment_path


	def verify_user_access_to_file(self, user):
		if self.method in VIP_IMAGES_LIST:
			return user.is_authenticated() and user.account.verified and user.has_perm('matrr.view_vip_images')
		return user.is_authenticated() and user.account.verified

	def frag(self):
		return os.path.basename(self.html_fragment.name)

	def __unicode__(self):
		# You should override this method too
		return "%s.(%s)" % (self.title, 'MATRRImage')

	def populate_svg(self):
		return

	class Meta:
		abstract = True


#  This model breaks MATRR field name scheme
class MTDImage(MATRRImage):
	mdi_id = models.AutoField(primary_key=True)
	monkey_to_drinking_experiment = models.ForeignKey(MonkeyToDrinkingExperiment, null=False, related_name='image_set', editable=False)
	objects = VIPManager()

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
	objects = VIPManager()

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
		return "%s.%s.(%s)" % (self.monkey.__unicode__(), self.title, str(self.pk))

	class Meta:
		permissions = (
			('view_vip_images', 'Can view VIP images'),
			)
		db_table = 'mig_monkey_image'


#  This model breaks MATRR field name scheme
class CohortImage(MATRRImage):
	cig_id = models.AutoField(primary_key=True)
	cohort = models.ForeignKey(Cohort, null=False, related_name='image_set', editable=False)
	objects = VIPManager()

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
		if self.tst_sex_relevant != TissueTypeSexRelevant.Both:
			if monkey.mky_gender != self.tst_sex_relevant:
				return Availability.Unavailable

		if monkey.cohort.coh_upcoming:
		#			just idea: is possible a situation when we know that some tissue of this monkey will never be in stock?
		# 			if yes, we should probably track it somehow and reflect here, but not important right now
			return Availability.Available

		tissue_samples = TissueSample.objects.filter(monkey=monkey, tissue_type=self)

		for tissue_sample in tissue_samples:
			if tissue_sample.tss_sample_quantity > 0 or tissue_sample.tss_sample_quantity is None:
			#		returns In_stock if any of the samples is present and its amount is positive
			#		does not reflect accepted requests
				return Availability.In_Stock

		if 'custom' in self.tst_tissue_name.lower():
			return Availability.Available
		return Availability.Unavailable

	def get_pending_request_count(self, monkey):
		return self.tissue_request_set.filter(req_request__req_status=RequestStatus.Submitted).count()

	def get_accepted_request_count(self, monkey):
		return self.tissue_request_set.filter(req_request__req_status=RequestStatus.Accepted).count()

	class Meta:
		db_table = 'tst_tissue_types'
		unique_together = (('tst_tissue_name', 'category'),)
		permissions = (
		('browse_inventory', 'Can browse inventory'),
		)


class RequestManager(models.Manager):
	def processed(self):
		return self.get_query_set().exclude(req_status=RequestStatus.Cart).exclude(req_status=RequestStatus.Revised)

	def evaluated(self):
		return self.get_query_set().exclude(req_status=RequestStatus.Cart).exclude(req_status=RequestStatus.Revised).exclude(
			req_status=RequestStatus.Submitted)

	def revised(self):
		return self.get_query_set().filter(req_status=RequestStatus.Revised)

	def submitted(self):
		return self.get_query_set().filter(req_status=RequestStatus.Submitted)

	def shipped(self):
		return self.get_query_set().filter(req_status=RequestStatus.Shipped)

	def accepted_and_partially(self):
		return self.get_query_set().filter(Q(req_status=RequestStatus.Accepted) | Q(req_status=RequestStatus.Partially))

	def cart(self):
		return self.get_query_set().filter(req_status=RequestStatus.Cart)


class Request(models.Model, DiffingMixin):
	########  BIG IMPORTANT WARNING  #######
	# If you're adding new fields to this model
	# Don't forget to exclude them from any applicable Form
	########

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

	req_purchase_order = models.CharField("Purchase Order", max_length=200, null=True, blank=True)
#	req_estimated_cost = models.IntegerField("Estimated cost", null=True, blank=True)

	def __unicode__(self):
		return 'User: ' + self.user.username +\
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

	def create_revised_duplicate(self):
		kwargs = {}
		# this does not capture m2m fields or other models with FK refs to Request
		for field in self._meta.fields:
			if field.name != 'req_request_id': # do not duplicate the primary key
				kwargs[field.name] = self.__getattribute__(field.name)
		revised = Request.objects.create(**kwargs)
		# Don't duplicate some other fields
		revised.req_modified_date = datetime.now()
		revised.req_status = RequestStatus.Revised
		revised.req_report_asked = False
		revised.parent_request = self

		# Duplicate all TissueRequests
		revised.save() # save() must be called before the forloop and m2m assignment
		tr_duplicates = []
		for tissue_request in self.tissue_request_set.all():
			if not tissue_request.is_fully_accepted():
				tr_duplicates.append(tissue_request.create_revised_duplicate(revised))
		revised.tissue_request_set = tr_duplicates
		revised.req_estimated_cost = None
		revised.save()
		return revised

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
			 self._original_state['req_status'] == RequestStatus.Revised):
			self.req_request_date = datetime.now()
		self.req_modified_date = datetime.now()
		self._previous_status = self._original_state['req_status']
		super(Request, self).save(force_insert, force_update, using)

	def can_be_revised(self):
		if self.req_status == RequestStatus.Rejected or self.req_status == RequestStatus.Partially:
			return True
		return False

	def can_be_edited(self):
		if self.req_status == RequestStatus.Revised:
			return True
		return False

	def is_processed(self):
		if self.req_status != RequestStatus.Cart and self.req_status != RequestStatus.Revised:
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
			if self.user.account.has_mta() and self.req_purchase_order:
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
	request = models.ForeignKey(Request, related_name='rud_set', db_column='req_id', null=False, blank=False,
								help_text='Choose a shipped request for which you would like to upload a research update:')
	rud_date = models.DateField('Date uploaded', editable=False, blank=True, null=True, auto_now_add=True)
	rud_title = models.CharField('Title', blank=True, null=False, max_length=25,
								 help_text='Give your research update a short name to make it easier for you to reference.')
	rud_file = models.FileField('Selected file', upload_to='rud/', default='', null=False, blank=False,
								help_text='File to Upload')

	def __unicode__(self):
		return "%s: %s (%s)" % (self.request.__unicode__(), self.rud_title, self.rud_file.name)

	def verify_user_access_to_file(self, user):
		if self.request.user == user:
			return True
		if user.has_perm('matrr.view_rud_file'):
			return True
		return False

	class Meta:
		db_table = 'rud_research_update'
		permissions = (
		('view_rud_file', 'Can view research update files of other users'),
		)


class TissueRequest(models.Model):
	rtt_tissue_request_id = models.AutoField(primary_key=True)
	req_request = models.ForeignKey(Request, null=False, related_name='tissue_request_set', db_column='req_request_id')
	tissue_type = models.ForeignKey(TissueType, null=False, related_name='tissue_request_set', db_column='tst_type_id')
	rtt_fix_type = models.CharField('Fixation', null=False, blank=False,
									max_length=200,
									help_text='Please select the appropriate fix type.')
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
		if self.rtt_fix_type != "Flash Frozen":
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

		if self.req_request.pk == 100:
			return 3600
		if self.req_request.pk in (169, 170):
			return 2400
		if self.req_request.pk in (171, 172):
			return 1400
		
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
		duplicate = TissueRequest() # I don't know why this worked for TissueRequest but not Request
		# this does not capture M2M fields or other models with FK refs to TissueRequest
		for field in self._meta.fields:
			if field.name != 'rtt_tissue_request_id': # do not duplicate the primary key
				duplicate.__setattr__(field.name, self.__getattribute__(field.name))



		# Update the request FK with the new revised request
		duplicate.req_request = revised_request
		# And duplicate the requested and accepted monkeys
		duplicate.save() # Must have a PK before doing m2m stuff

		for a in self.accepted_monkeys.all():
			duplicate.previously_accepted_monkeys.add(a)
		duplicate.accepted_monkeys.clear()
		#		duplicate.accepted_monkeys = self.accepted_monkeys.all()
		if self.is_partially_accepted():
			monk = list()
			for m in self.monkeys.all():
				if m not in self.accepted_monkeys.all():
					monk.append(m)
			duplicate.monkeys = monk
		else:
			duplicate.monkeys = self.monkeys.all()

		duplicate.save()
		return duplicate

	def cart_display(self):
		return self.tissue_type.tst_tissue_name

	def save(self, *args, **kwargs):
		super(TissueRequest, self).save(*args, **kwargs)
		if self.rtt_tissue_request_id is None and self.tissue_type.category.cat_name == 'Custom':
			# if this is a custom request and it hasn't been saved yet
			# set the increment to the correct amount
			self.rtt_custom_increment = TissueRequest.objects.filter(req_request=self.req_request,
																	 tissue_type__category__cat_name='Custom').count()

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
	tissue_type = models.ForeignKey(TissueType, db_column='tst_type_id',
									related_name='tissue_sample_set',
									blank=False, null=False)
	monkey = models.ForeignKey(Monkey, db_column='mky_id',
							   related_name='tissue_sample_set',
							   blank=False, null=False)
	tss_freezer = models.CharField('Freezer Name',
								   max_length=100,
								   null=False, blank=True,
								   help_text='Please enter the name of the freezer this sample is in.')
	tss_location = models.CharField('Location of Sample',
									max_length=100,
									null=False, blank=True,
									help_text='Please enter the location in the freezer where this sample is stored.')
	tss_details = models.TextField('Details',
								   null=True, blank=True,
								   help_text='Any extras details about this tissue sample.')
	tss_sample_quantity = models.FloatField('Sample Quantity', null=True, default=0)
	tss_units = models.CharField('Quantity units',
								 choices=Units, null=False, max_length=20, default=Units[3][0])
	tss_modified = models.DateTimeField('Last Updated', auto_now_add=True, editable=False, auto_now=True)
	user = models.ForeignKey(User, verbose_name="Last Updated by", on_delete=models.SET_NULL, related_name='+', db_column='usr_usr_id', editable=False, null=True)


	def get_modified(self):
		return self.tss_modified

	def __unicode__(self):
		return str(self.monkey) + ' ' + str(self.tissue_type) + ' ' + self.tss_freezer\
			   + ': ' + self.tss_location + ' (' + str(self.get_quantity()) + ' ' + self.get_tss_units_display() + ')'

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
	monkey = models.OneToOneField(Monkey, null=False, blank=False, related_name='genealogy', primary_key=True)
	sire = models.ForeignKey('self', null=True, blank=True, related_name='+')
	dam = models.ForeignKey('self', null=True, blank=True, related_name='+')
	relationships = models.ManyToManyField('self', symmetrical=False, null=True, blank=True, through='FamilyRelationship', related_name='+')

	def create_parent_relationships(self):
		if self.sire:
			fathers_son = FamilyRelationship.objects.get_or_create(me=self, relative=self.sire, fmr_type=FamilyRelationship.RELATIONSHIP.Offspring)[0]
			sons_father = FamilyRelationship.objects.get_or_create(relative=self, me=self.sire, fmr_type=FamilyRelationship.RELATIONSHIP.Parent)[0]
		if self.dam:
			mothers_son = FamilyRelationship.objects.get_or_create(me=self, relative=self.dam, fmr_type=FamilyRelationship.RELATIONSHIP.Offspring)[0]
			sons_mother = FamilyRelationship.objects.get_or_create(relative=self, me=self.dam, fmr_type=FamilyRelationship.RELATIONSHIP.Parent)[0]

	class Meta:
		db_table = 'fmn_family_node'


class FamilyRelationship(models.Model):
	RELATIONSHIP = Enumeration([('P', 'Parent', 'Parent'),('O', 'Offspring', 'Offspring')])
	fmr_id = models.AutoField(primary_key=True)
	me = models.ForeignKey(FamilyNode, related_name='+', null=False, blank=False)
	relative = models.ForeignKey(FamilyNode, related_name='relatives', null=False, blank=False)
	fmr_type = models.CharField('Relationship Type', max_length=2, choices=RELATIONSHIP)
	fmr_coeff = models.FloatField('Relationship Coefficient', blank=False, null=True, default=None)


	#  There are going to be 2 records in this table for each relationship, source <-> target.   The type of relationship gets tricky to define.
	#  (Grand)Parents are easy to define, but aunts/uncles/cousins/halfcousins/halfsiblings and it continues to get worse.
	#  Plotting _a_ monkey's lineage should be easy.  Plotting two monkey's relationship to each other is gonna be nuts.
	class Meta:
		db_table = 'fmr_family_relationship'




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
	if (previous_status == RequestStatus.Cart or previous_status == RequestStatus.Revised)\
	and current_status == RequestStatus.Submitted:
		from utils.regular_tasks.send_new_request_info import send_new_request_info
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
				from utils.regular_tasks.send_verification_complete_notification import send_verification_complete_notification
				send_verification_complete_notification(req_request)

