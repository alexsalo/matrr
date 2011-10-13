# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Adding model 'Institution'
        db.create_table('ins_institutions', (
            ('ins_institution_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ins_institution_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
        ))
        db.send_create_signal('matrr', ['Institution'])

        # Adding model 'EventType'
        db.create_table('evt_event_types', (
            ('evt_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('evt_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('evt_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['EventType'])

        # Adding model 'Cohort'
        db.create_table('coh_cohorts', (
            ('coh_cohort_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('coh_cohort_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('coh_upcoming', self.gf('django.db.models.fields.BooleanField')(default=True)),
            ('institution', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cohort_set', db_column='ins_institution_id', to=orm['matrr.Institution'])),
            ('coh_species', self.gf('django.db.models.fields.CharField')(max_length=30)),
        ))
        db.send_create_signal('matrr', ['Cohort'])

        # Adding model 'CohortEvent'
        db.create_table('cev_cohort_events', (
            ('cev_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cohort', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cohort_event_set', db_column='coh_cohort_id', to=orm['matrr.Cohort'])),
            ('event', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cohort_event_set', db_column='evt_id', to=orm['matrr.EventType'])),
            ('cev_date', self.gf('django.db.models.fields.DateField')()),
            ('cev_info', self.gf('django.db.models.fields.CharField')(max_length=200, null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['CohortEvent'])

        # Adding model 'Monkey'
        db.create_table('mky_monkeys', (
            ('mky_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cohort', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['matrr.Cohort'], db_column='coh_cohort_id')),
            ('mky_real_id', self.gf('django.db.models.fields.IntegerField')(unique=True)),
            ('mky_name', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('mky_gender', self.gf('django.db.models.fields.CharField')(max_length=1, null=True, blank=True)),
            ('mky_birthdate', self.gf('django.db.models.fields.CharField')(max_length=20, null=True, blank=True)),
            ('mky_weight', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('mky_drinking', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('mky_housing_control', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('mky_necropsy_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('mky_study_complete', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('mky_stress_model', self.gf('django.db.models.fields.CharField')(max_length=30, null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['Monkey'])

        # Adding model 'Mta'
        db.create_table('mta_material_transfer', (
            ('mta_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='mta_set', blank=True, db_column='usr_id', to=orm['auth.User'])),
            ('mta_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
            ('mta_title', self.gf('django.db.models.fields.CharField')(max_length=25, blank=True)),
            ('mta_file', self.gf('django.db.models.fields.files.FileField')(default='', max_length=100)),
        ))
        db.send_create_signal('matrr', ['Mta'])

        # Adding model 'Account'
        db.create_table('act_account', (
            ('user', self.gf('django.db.models.fields.related.OneToOneField')(related_name='account', unique=True, primary_key=True, db_column='usr_usr_id', to=orm['auth.User'])),
            ('act_shipping_name', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True)),
            ('act_address1', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('act_address2', self.gf('django.db.models.fields.CharField')(max_length=50, null=True, blank=True)),
            ('act_city', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True)),
            ('act_state', self.gf('django.db.models.fields.CharField')(max_length=2, null=True, blank=True)),
            ('act_zip', self.gf('django.db.models.fields.CharField')(max_length=10, null=True, blank=True)),
            ('act_country', self.gf('django.db.models.fields.CharField')(max_length=25, null=True, blank=True)),
            ('act_fedex', self.gf('django.db.models.fields.CharField')(max_length=9, null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['Account'])

        # Adding model 'DrinkingExperiment'
        db.create_table('dex_drinking_experiments', (
            ('dex_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cohort', self.gf('django.db.models.fields.related.ForeignKey')(related_name='cohort_drinking_experiment_set', db_column='coh_cohort_id', to=orm['matrr.Cohort'])),
            ('dex_date', self.gf('django.db.models.fields.DateField')()),
            ('dex_type', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('dex_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['DrinkingExperiment'])

        # Adding model 'MonkeyToDrinkingExperiment'
        db.create_table('mtd_monkeys_to_drinking_experiments', (
            ('mtd_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('drinking_experiment', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='dex_id', to=orm['matrr.DrinkingExperiment'])),
            ('mtd_etoh_intake', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('mtd_veh_intake', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('mtd_total_pellets', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('mtd_weight', self.gf('django.db.models.fields.FloatField')(null=True, blank=True)),
            ('mtd_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['MonkeyToDrinkingExperiment'])

        # Adding model 'RequestStatus'
        db.create_table('rqs_request_statuses', (
            ('rqs_status_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rqs_status_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('rqs_status_description', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('matrr', ['RequestStatus'])

        # Adding model 'TissueType'
        db.create_table('tst_tissue_types', (
            ('tst_type_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tst_tissue_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('tst_description', self.gf('django.db.models.fields.TextField')(null=True)),
            ('tst_count_per_monkey', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['TissueType'])

        # Adding M2M table for field unavailable_list on 'TissueType'
        db.create_table('ttu_tissue_types_unavailable', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tissuetype', models.ForeignKey(orm['matrr.tissuetype'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('ttu_tissue_types_unavailable', ['tissuetype_id', 'monkey_id'])

        # Adding model 'Unit'
        db.create_table('unt_units', (
            ('unt_unit_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('unt_unit_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
        ))
        db.send_create_signal('matrr', ['Unit'])

        # Adding model 'Request'
        db.create_table('req_requests', (
            ('req_request_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('request_status', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['matrr.RequestStatus'], db_column='rqs_status_id')),
            ('cohort', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['matrr.Cohort'], db_column='coh_cohort_id')),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], db_column='usr_user_id')),
            ('req_modified_date', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('req_request_date', self.gf('django.db.models.fields.DateTimeField')(auto_now_add=True, blank=True)),
            ('req_experimental_plan', self.gf('django.db.models.fields.files.FileField')(default='', max_length=100, null=True, blank=True)),
            ('req_project_title', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('req_reason', self.gf('django.db.models.fields.TextField')()),
            ('req_progress_agreement', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('req_referred_by', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('req_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['Request'])

        # Adding model 'RequestRevision'
        db.create_table('rqv_request_revisions', (
            ('rqv_request_revision_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('req_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='request_revision_set', db_column='req_request_id', to=orm['matrr.Request'])),
            ('rqv_version_number', self.gf('django.db.models.fields.IntegerField')()),
            ('rqv_request_date', self.gf('django.db.models.fields.DateTimeField')()),
            ('rqv_experimental_plan', self.gf('django.db.models.fields.files.FileField')(max_length=100)),
            ('rqv_notes', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('matrr', ['RequestRevision'])

        # Adding unique constraint on 'RequestRevision', fields ['req_request', 'rqv_version_number']
        db.create_unique('rqv_request_revisions', ['req_request_id', 'rqv_version_number'])

        # Adding model 'TissueRequest'
        db.create_table('rtt_requests_to_tissue_types', (
            ('rtt_tissue_request_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('req_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tissue_request_set', db_column='req_request_id', to=orm['matrr.Request'])),
            ('tissue_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tissue_request_set', db_column='tst_type_id', to=orm['matrr.TissueType'])),
            ('rtt_fix_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('rtt_amount', self.gf('django.db.models.fields.FloatField')()),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='unt_unit_id', to=orm['matrr.Unit'])),
            ('rtt_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['TissueRequest'])

        # Adding unique constraint on 'TissueRequest', fields ['req_request', 'tissue_type', 'rtt_fix_type']
        db.create_unique('rtt_requests_to_tissue_types', ['req_request_id', 'tst_type_id', 'rtt_fix_type'])

        # Adding M2M table for field monkeys on 'TissueRequest'
        db.create_table('mtr_monkeys_to_tissue_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tissuerequest', models.ForeignKey(orm['matrr.tissuerequest'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('mtr_monkeys_to_tissue_requests', ['tissuerequest_id', 'monkey_id'])

        # Adding model 'TissueRequestRevision'
        db.create_table('rtv_request_to_tissue_type_revisions', (
            ('rtv_tissue_request_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('request_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tissue_request_revision_set', db_column='rqv_request_revision_id', to=orm['matrr.RequestRevision'])),
            ('tissue_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tissue_request_revision_set', db_column='tst_type_id', to=orm['matrr.TissueType'])),
            ('rtv_fix_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('rtv_amount', self.gf('django.db.models.fields.FloatField')()),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='unt_unit_id', to=orm['matrr.Unit'])),
            ('rtv_notes', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('matrr', ['TissueRequestRevision'])

        # Adding M2M table for field monkeys on 'TissueRequestRevision'
        db.create_table('mtv_monkeys_to_tissue_request_revisions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('tissuerequestrevision', models.ForeignKey(orm['matrr.tissuerequestrevision'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('mtv_monkeys_to_tissue_request_revisions', ['tissuerequestrevision_id', 'monkey_id'])

        # Adding model 'BrainBlock'
        db.create_table('bbl_brain_blocks', (
            ('bbl_block_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bbl_block_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('bbl_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BrainBlock'])

        # Adding model 'BrainRegion'
        db.create_table('bre_brain_regions', (
            ('bre_region_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bre_region_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('bre_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('bre_count_per_monkey', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BrainRegion'])

        # Adding M2M table for field unavailable_list on 'BrainRegion'
        db.create_table('bru_brain_regions_unavailable', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('brainregion', models.ForeignKey(orm['matrr.brainregion'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('bru_brain_regions_unavailable', ['brainregion_id', 'monkey_id'])

        # Adding model 'BrainRegionRequest'
        db.create_table('rbr_requests_to_brain_regions', (
            ('rbr_region_request_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('req_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_set', db_column='req_request_id', to=orm['matrr.Request'])),
            ('brain_region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_set', db_column='bre_region_id', to=orm['matrr.BrainRegion'])),
            ('rbr_fix_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('rbr_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BrainRegionRequest'])

        # Adding unique constraint on 'BrainRegionRequest', fields ['req_request', 'brain_region']
        db.create_unique('rbr_requests_to_brain_regions', ['req_request_id', 'bre_region_id'])

        # Adding M2M table for field monkeys on 'BrainRegionRequest'
        db.create_table('mbr_monkeys_to_brain_region_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('brainregionrequest', models.ForeignKey(orm['matrr.brainregionrequest'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('mbr_monkeys_to_brain_region_requests', ['brainregionrequest_id', 'monkey_id'])

        # Adding model 'BrainRegionRequestRevision'
        db.create_table('rbv_requests_to_brain_regions_revisions', (
            ('rbv_revision_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('request_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_revision_set', db_column='rqv_request_revision_id', to=orm['matrr.RequestRevision'])),
            ('brain_region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_revision_set', db_column='bbl_block_id', to=orm['matrr.BrainRegion'])),
            ('brv_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BrainRegionRequestRevision'])

        # Adding unique constraint on 'BrainRegionRequestRevision', fields ['request_revision', 'brain_region']
        db.create_unique('rbv_requests_to_brain_regions_revisions', ['rqv_request_revision_id', 'bbl_block_id'])

        # Adding M2M table for field monkeys on 'BrainRegionRequestRevision'
        db.create_table('mrv_monkeys_to_brain_region_request_revisions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('brainregionrequestrevision', models.ForeignKey(orm['matrr.brainregionrequestrevision'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('mrv_monkeys_to_brain_region_request_revisions', ['brainregionrequestrevision_id', 'monkey_id'])

        # Adding model 'BloodAndGenetic'
        db.create_table('bag_blood_and_genetics', (
            ('bag_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bag_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('bag_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('bag_count_per_monkey', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BloodAndGenetic'])

        # Adding M2M table for field unavailable_list on 'BloodAndGenetic'
        db.create_table('bgu_blood_and_genetics_unavailable', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bloodandgenetic', models.ForeignKey(orm['matrr.bloodandgenetic'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('bgu_blood_and_genetics_unavailable', ['bloodandgenetic_id', 'monkey_id'])

        # Adding model 'BloodAndGeneticRequest'
        db.create_table('rbg_requests_to_blood_and_genetics', (
            ('rbg_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('req_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_and_genetic_request_set', db_column='req_request_id', to=orm['matrr.Request'])),
            ('blood_genetic_item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_and_genetic_request_set', db_column='bag_id', to=orm['matrr.BloodAndGenetic'])),
            ('rbg_amount', self.gf('django.db.models.fields.FloatField')()),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='unt_unit_id', to=orm['matrr.Unit'])),
            ('rbg_fix_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('rbg_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BloodAndGeneticRequest'])

        # Adding unique constraint on 'BloodAndGeneticRequest', fields ['req_request', 'blood_genetic_item']
        db.create_unique('rbg_requests_to_blood_and_genetics', ['req_request_id', 'bag_id'])

        # Adding M2M table for field monkeys on 'BloodAndGeneticRequest'
        db.create_table('mgr_monkeys_to_blood_and_genetic_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bloodandgeneticrequest', models.ForeignKey(orm['matrr.bloodandgeneticrequest'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('mgr_monkeys_to_blood_and_genetic_requests', ['bloodandgeneticrequest_id', 'monkey_id'])

        # Adding model 'BloodAndGeneticRequestRevision'
        db.create_table('grr_requests_to_blood_and_genetic_revisions', (
            ('grr_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('request_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_and_genetic_request_revision_set', db_column='rqv_request_revision_id', to=orm['matrr.RequestRevision'])),
            ('blood_genetic_item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_and_genetic_request_revision_set', db_column='bag_id', to=orm['matrr.BloodAndGenetic'])),
            ('grr_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BloodAndGeneticRequestRevision'])

        # Adding unique constraint on 'BloodAndGeneticRequestRevision', fields ['request_revision', 'blood_genetic_item']
        db.create_unique('grr_requests_to_blood_and_genetic_revisions', ['rqv_request_revision_id', 'bag_id'])

        # Adding M2M table for field monkeys on 'BloodAndGeneticRequestRevision'
        db.create_table('mgv_monkeys_to_blood_genetic_request_revisions', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bloodandgeneticrequestrevision', models.ForeignKey(orm['matrr.bloodandgeneticrequestrevision'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('mgv_monkeys_to_blood_genetic_request_revisions', ['bloodandgeneticrequestrevision_id', 'monkey_id'])

        # Adding model 'CustomTissueRequest'
        db.create_table('ctr_custom_tissue_requests', (
            ('ctr_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('req_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='custom_tissue_request_set', db_column='req_request_id', to=orm['matrr.Request'])),
            ('ctr_description', self.gf('django.db.models.fields.TextField')()),
            ('ctr_fix_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('ctr_amount', self.gf('django.db.models.fields.FloatField')()),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='unt_unit_id', to=orm['matrr.Unit'])),
        ))
        db.send_create_signal('matrr', ['CustomTissueRequest'])

        # Adding M2M table for field monkeys on 'CustomTissueRequest'
        db.create_table('mcr_monkeys_to_custom_tissue_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('customtissuerequest', models.ForeignKey(orm['matrr.customtissuerequest'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('mcr_monkeys_to_custom_tissue_requests', ['customtissuerequest_id', 'monkey_id'])

        # Adding model 'Event'
        db.create_table('matrr_event', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('date', self.gf('django.db.models.fields.DateField')()),
        ))
        db.send_create_signal('matrr', ['Event'])

        # Adding model 'Review'
        db.create_table('rvs_reviews', (
            ('rvs_review_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('req_request', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['matrr.Request'], db_column='req_request_id')),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(to=orm['auth.User'], db_column='usr_user_id')),
            ('rvs_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['Review'])

        # Adding unique constraint on 'Review', fields ['user', 'req_request']
        db.create_unique('rvs_reviews', ['usr_user_id', 'req_request_id'])

        # Adding model 'ReviewRevision'
        db.create_table('rvr_review_revisions', (
            ('rvr_revision_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('review', self.gf('django.db.models.fields.related.ForeignKey')(related_name='review_revision_set', db_column='rvs_review_id', to=orm['matrr.Review'])),
            ('request_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='review_revision_set', db_column='rqv_request_revision_id', to=orm['matrr.RequestRevision'])),
            ('rvr_notes', self.gf('django.db.models.fields.TextField')(null=True)),
        ))
        db.send_create_signal('matrr', ['ReviewRevision'])

        # Adding unique constraint on 'ReviewRevision', fields ['review', 'request_revision']
        db.create_unique('rvr_review_revisions', ['rvs_review_id', 'rqv_request_revision_id'])

        # Adding model 'TissueRequestReview'
        db.create_table('vtr_reviews_to_tissue_requests', (
            ('vtr_request_review_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('review', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tissue_request_review_set', db_column='rvs_review_id', to=orm['matrr.Review'])),
            ('tissue_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tissue_request_review_set', db_column='rtt_tissue_request_id', to=orm['matrr.TissueRequest'])),
            ('vtr_scientific_merit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vtr_quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vtr_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vtr_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['TissueRequestReview'])

        # Adding unique constraint on 'TissueRequestReview', fields ['review', 'tissue_request']
        db.create_unique('vtr_reviews_to_tissue_requests', ['rvs_review_id', 'rtt_tissue_request_id'])

        # Adding model 'TissueRequestReviewRevision'
        db.create_table('vtv_reviews_to_tissue_request_revisions', (
            ('vtv_review_revision_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('review_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tissue_request_review_revision_set', db_column='rvr_revision_id', to=orm['matrr.ReviewRevision'])),
            ('tissue_request_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tissue_request_review_revision_set', db_column='rtv_tissue_request_id', to=orm['matrr.TissueRequestRevision'])),
            ('vtv_scientific_merit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vtv_quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vtv_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vtv_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['TissueRequestReviewRevision'])

        # Adding unique constraint on 'TissueRequestReviewRevision', fields ['review_revision', 'tissue_request_revision']
        db.create_unique('vtv_reviews_to_tissue_request_revisions', ['rvr_revision_id', 'rtv_tissue_request_id'])

        # Adding model 'BrainRegionRequestReview'
        db.create_table('vbr_reviews_to_brain_region_requests', (
            ('vbr_region_request_review_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('review', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_review_set', db_column='rvs_review_id', to=orm['matrr.Review'])),
            ('brain_region_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_review_set', db_column='rbr_region_request_id', to=orm['matrr.BrainRegionRequest'])),
            ('vbr_scientific_merit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vbr_quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vbr_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vbr_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BrainRegionRequestReview'])

        # Adding unique constraint on 'BrainRegionRequestReview', fields ['review', 'brain_region_request']
        db.create_unique('vbr_reviews_to_brain_region_requests', ['rvs_review_id', 'rbr_region_request_id'])

        # Adding model 'BrainRegionRequestReviewRevision'
        db.create_table('vrv_reviews_to_brain_region_request_revisions', (
            ('vrv_review_revision_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('review_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_review_revision_set', db_column='rvr_revision_id', to=orm['matrr.ReviewRevision'])),
            ('brain_region_request_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_review_revision_set', db_column='rbv_revision_id', to=orm['matrr.BrainRegionRequestRevision'])),
            ('vrv_scientific_merit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vrv_quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vrv_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vrv_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BrainRegionRequestReviewRevision'])

        # Adding unique constraint on 'BrainRegionRequestReviewRevision', fields ['review_revision', 'brain_region_request_revision']
        db.create_unique('vrv_reviews_to_brain_region_request_revisions', ['rvr_revision_id', 'rbv_revision_id'])

        # Adding model 'BloodAndGeneticRequestReview'
        db.create_table('vbg_reviews_to_blood_and_genetic_requests', (
            ('vbg_blood_genetic_request_review_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('review', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_and_genetic_request_review_set', db_column='rvs_review_id', to=orm['matrr.Review'])),
            ('blood_and_genetic_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_and_genetic_request_review_set', db_column='rbg_id', to=orm['matrr.BloodAndGeneticRequest'])),
            ('vbg_scientific_merit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vbg_quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vbg_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vbg_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BloodAndGeneticRequestReview'])

        # Adding unique constraint on 'BloodAndGeneticRequestReview', fields ['review', 'blood_and_genetic_request']
        db.create_unique('vbg_reviews_to_blood_and_genetic_requests', ['rvs_review_id', 'rbg_id'])

        # Adding model 'BloodAndGeneticRequestReviewRevision'
        db.create_table('vgv_reviews_to_blood_and_genetic_request_revisions', (
            ('vgv_review_revision_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('review_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_genetic_request_review_revision_set', db_column='rvr_revision_id', to=orm['matrr.ReviewRevision'])),
            ('blood_and_genetic_request_revision', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_genetic_request_review_revision_set', db_column='mrv_id', to=orm['matrr.BloodAndGeneticRequestRevision'])),
            ('vgv_scientific_merit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vgv_quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vgv_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vgv_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BloodAndGeneticRequestReviewRevision'])

        # Adding unique constraint on 'BloodAndGeneticRequestReviewRevision', fields ['review_revision', 'blood_and_genetic_request_revision']
        db.create_unique('vgv_reviews_to_blood_and_genetic_request_revisions', ['rvr_revision_id', 'mrv_id'])

        # Adding model 'CustomTissueRequestReview'
        db.create_table('vct_reviews_to_custom_tissue_requests', (
            ('vct_review_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('review', self.gf('django.db.models.fields.related.ForeignKey')(related_name='custom_tissue_request_review_set', db_column='rvs_review_id', to=orm['matrr.Review'])),
            ('custom_tissue_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='custom_tissue_request_review_set', db_column='rbg_id', to=orm['matrr.CustomTissueRequest'])),
            ('vct_scientific_merit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vct_quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vct_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vct_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['CustomTissueRequestReview'])

        # Adding unique constraint on 'CustomTissueRequestReview', fields ['review', 'custom_tissue_request']
        db.create_unique('vct_reviews_to_custom_tissue_requests', ['rvs_review_id', 'rbg_id'])

        # Adding model 'Shipment'
        db.create_table('shp_shipments', (
            ('shp_shipment_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('user', self.gf('django.db.models.fields.related.ForeignKey')(related_name='shipment_set', to=orm['auth.User'])),
            ('req_request', self.gf('django.db.models.fields.related.OneToOneField')(related_name='shipment', unique=True, to=orm['matrr.Request'])),
            ('shp_tracking', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True)),
            ('shp_shipment_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['Shipment'])

        # Adding model 'PeripheralTissueSample'
        db.create_table('pts_peripheral_tissue_samples', (
            ('pts_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tissue_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='peripheral_sample_set', db_column='tst_type_id', to=orm['matrr.TissueType'])),
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='peripheral_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('pts_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('pts_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('pts_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['PeripheralTissueSample'])

        # Adding model 'BrainBlockSample'
        db.create_table('bbs_brain_block_samples', (
            ('bbs_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('brain_block', self.gf('django.db.models.fields.related.ForeignKey')(related_name='block_sample_set', db_column='bbl_block_id', to=orm['matrr.BrainBlock'])),
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='block_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('bbs_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('bbs_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('bbs_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BrainBlockSample'])

        # Adding model 'BrainRegionSample'
        db.create_table('brs_brain_region_samples', (
            ('brs_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('brain_region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='region_sample_set', db_column='bre_region_id', to=orm['matrr.BrainRegion'])),
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='region_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('brs_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('brs_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('brs_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BrainRegionSample'])

        # Adding model 'BloodAndGeneticsSample'
        db.create_table('bgs_blood_and_genetics_samples', (
            ('bgs_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('blood_genetic_item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_genetic_sample_set', db_column='bag_id', to=orm['matrr.BloodAndGenetic'])),
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_genetic_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('bgs_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('bgs_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('bgs_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BloodAndGeneticsSample'])

        # Adding model 'OtherTissueSample'
        db.create_table('ots_other_tissue_samples', (
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ots_description', self.gf('django.db.models.fields.TextField')()),
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='other_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('ots_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('ots_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('ots_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['OtherTissueSample'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'CustomTissueRequestReview', fields ['review', 'custom_tissue_request']
        db.delete_unique('vct_reviews_to_custom_tissue_requests', ['rvs_review_id', 'rbg_id'])

        # Removing unique constraint on 'BloodAndGeneticRequestReviewRevision', fields ['review_revision', 'blood_and_genetic_request_revision']
        db.delete_unique('vgv_reviews_to_blood_and_genetic_request_revisions', ['rvr_revision_id', 'mrv_id'])

        # Removing unique constraint on 'BloodAndGeneticRequestReview', fields ['review', 'blood_and_genetic_request']
        db.delete_unique('vbg_reviews_to_blood_and_genetic_requests', ['rvs_review_id', 'rbg_id'])

        # Removing unique constraint on 'BrainRegionRequestReviewRevision', fields ['review_revision', 'brain_region_request_revision']
        db.delete_unique('vrv_reviews_to_brain_region_request_revisions', ['rvr_revision_id', 'rbv_revision_id'])

        # Removing unique constraint on 'BrainRegionRequestReview', fields ['review', 'brain_region_request']
        db.delete_unique('vbr_reviews_to_brain_region_requests', ['rvs_review_id', 'rbr_region_request_id'])

        # Removing unique constraint on 'TissueRequestReviewRevision', fields ['review_revision', 'tissue_request_revision']
        db.delete_unique('vtv_reviews_to_tissue_request_revisions', ['rvr_revision_id', 'rtv_tissue_request_id'])

        # Removing unique constraint on 'TissueRequestReview', fields ['review', 'tissue_request']
        db.delete_unique('vtr_reviews_to_tissue_requests', ['rvs_review_id', 'rtt_tissue_request_id'])

        # Removing unique constraint on 'ReviewRevision', fields ['review', 'request_revision']
        db.delete_unique('rvr_review_revisions', ['rvs_review_id', 'rqv_request_revision_id'])

        # Removing unique constraint on 'Review', fields ['user', 'req_request']
        db.delete_unique('rvs_reviews', ['usr_user_id', 'req_request_id'])

        # Removing unique constraint on 'BloodAndGeneticRequestRevision', fields ['request_revision', 'blood_genetic_item']
        db.delete_unique('grr_requests_to_blood_and_genetic_revisions', ['rqv_request_revision_id', 'bag_id'])

        # Removing unique constraint on 'BloodAndGeneticRequest', fields ['req_request', 'blood_genetic_item']
        db.delete_unique('rbg_requests_to_blood_and_genetics', ['req_request_id', 'bag_id'])

        # Removing unique constraint on 'BrainRegionRequestRevision', fields ['request_revision', 'brain_region']
        db.delete_unique('rbv_requests_to_brain_regions_revisions', ['rqv_request_revision_id', 'bbl_block_id'])

        # Removing unique constraint on 'BrainRegionRequest', fields ['req_request', 'brain_region']
        db.delete_unique('rbr_requests_to_brain_regions', ['req_request_id', 'bre_region_id'])

        # Removing unique constraint on 'TissueRequest', fields ['req_request', 'tissue_type', 'rtt_fix_type']
        db.delete_unique('rtt_requests_to_tissue_types', ['req_request_id', 'tst_type_id', 'rtt_fix_type'])

        # Removing unique constraint on 'RequestRevision', fields ['req_request', 'rqv_version_number']
        db.delete_unique('rqv_request_revisions', ['req_request_id', 'rqv_version_number'])

        # Deleting model 'Institution'
        db.delete_table('ins_institutions')

        # Deleting model 'EventType'
        db.delete_table('evt_event_types')

        # Deleting model 'Cohort'
        db.delete_table('coh_cohorts')

        # Deleting model 'CohortEvent'
        db.delete_table('cev_cohort_events')

        # Deleting model 'Monkey'
        db.delete_table('mky_monkeys')

        # Deleting model 'Mta'
        db.delete_table('mta_material_transfer')

        # Deleting model 'Account'
        db.delete_table('act_account')

        # Deleting model 'DrinkingExperiment'
        db.delete_table('dex_drinking_experiments')

        # Deleting model 'MonkeyToDrinkingExperiment'
        db.delete_table('mtd_monkeys_to_drinking_experiments')

        # Deleting model 'RequestStatus'
        db.delete_table('rqs_request_statuses')

        # Deleting model 'TissueType'
        db.delete_table('tst_tissue_types')

        # Removing M2M table for field unavailable_list on 'TissueType'
        db.delete_table('ttu_tissue_types_unavailable')

        # Deleting model 'Unit'
        db.delete_table('unt_units')

        # Deleting model 'Request'
        db.delete_table('req_requests')

        # Deleting model 'RequestRevision'
        db.delete_table('rqv_request_revisions')

        # Deleting model 'TissueRequest'
        db.delete_table('rtt_requests_to_tissue_types')

        # Removing M2M table for field monkeys on 'TissueRequest'
        db.delete_table('mtr_monkeys_to_tissue_requests')

        # Deleting model 'TissueRequestRevision'
        db.delete_table('rtv_request_to_tissue_type_revisions')

        # Removing M2M table for field monkeys on 'TissueRequestRevision'
        db.delete_table('mtv_monkeys_to_tissue_request_revisions')

        # Deleting model 'BrainBlock'
        db.delete_table('bbl_brain_blocks')

        # Deleting model 'BrainRegion'
        db.delete_table('bre_brain_regions')

        # Removing M2M table for field unavailable_list on 'BrainRegion'
        db.delete_table('bru_brain_regions_unavailable')

        # Deleting model 'BrainRegionRequest'
        db.delete_table('rbr_requests_to_brain_regions')

        # Removing M2M table for field monkeys on 'BrainRegionRequest'
        db.delete_table('mbr_monkeys_to_brain_region_requests')

        # Deleting model 'BrainRegionRequestRevision'
        db.delete_table('rbv_requests_to_brain_regions_revisions')

        # Removing M2M table for field monkeys on 'BrainRegionRequestRevision'
        db.delete_table('mrv_monkeys_to_brain_region_request_revisions')

        # Deleting model 'BloodAndGenetic'
        db.delete_table('bag_blood_and_genetics')

        # Removing M2M table for field unavailable_list on 'BloodAndGenetic'
        db.delete_table('bgu_blood_and_genetics_unavailable')

        # Deleting model 'BloodAndGeneticRequest'
        db.delete_table('rbg_requests_to_blood_and_genetics')

        # Removing M2M table for field monkeys on 'BloodAndGeneticRequest'
        db.delete_table('mgr_monkeys_to_blood_and_genetic_requests')

        # Deleting model 'BloodAndGeneticRequestRevision'
        db.delete_table('grr_requests_to_blood_and_genetic_revisions')

        # Removing M2M table for field monkeys on 'BloodAndGeneticRequestRevision'
        db.delete_table('mgv_monkeys_to_blood_genetic_request_revisions')

        # Deleting model 'CustomTissueRequest'
        db.delete_table('ctr_custom_tissue_requests')

        # Removing M2M table for field monkeys on 'CustomTissueRequest'
        db.delete_table('mcr_monkeys_to_custom_tissue_requests')

        # Deleting model 'Event'
        db.delete_table('matrr_event')

        # Deleting model 'Review'
        db.delete_table('rvs_reviews')

        # Deleting model 'ReviewRevision'
        db.delete_table('rvr_review_revisions')

        # Deleting model 'TissueRequestReview'
        db.delete_table('vtr_reviews_to_tissue_requests')

        # Deleting model 'TissueRequestReviewRevision'
        db.delete_table('vtv_reviews_to_tissue_request_revisions')

        # Deleting model 'BrainRegionRequestReview'
        db.delete_table('vbr_reviews_to_brain_region_requests')

        # Deleting model 'BrainRegionRequestReviewRevision'
        db.delete_table('vrv_reviews_to_brain_region_request_revisions')

        # Deleting model 'BloodAndGeneticRequestReview'
        db.delete_table('vbg_reviews_to_blood_and_genetic_requests')

        # Deleting model 'BloodAndGeneticRequestReviewRevision'
        db.delete_table('vgv_reviews_to_blood_and_genetic_request_revisions')

        # Deleting model 'CustomTissueRequestReview'
        db.delete_table('vct_reviews_to_custom_tissue_requests')

        # Deleting model 'Shipment'
        db.delete_table('shp_shipments')

        # Deleting model 'PeripheralTissueSample'
        db.delete_table('pts_peripheral_tissue_samples')

        # Deleting model 'BrainBlockSample'
        db.delete_table('bbs_brain_block_samples')

        # Deleting model 'BrainRegionSample'
        db.delete_table('brs_brain_region_samples')

        # Deleting model 'BloodAndGeneticsSample'
        db.delete_table('bgs_blood_and_genetics_samples')

        # Deleting model 'OtherTissueSample'
        db.delete_table('ots_other_tissue_samples')


    models = {
        'auth.group': {
            'Meta': {'object_name': 'Group'},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '80'}),
            'permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'})
        },
        'auth.permission': {
            'Meta': {'ordering': "('content_type__app_label', 'content_type__model', 'codename')", 'unique_together': "(('content_type', 'codename'),)", 'object_name': 'Permission'},
            'codename': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'content_type': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['contenttypes.ContentType']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'auth.user': {
            'Meta': {'object_name': 'User'},
            'date_joined': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'email': ('django.db.models.fields.EmailField', [], {'max_length': '75', 'blank': 'True'}),
            'first_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'groups': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Group']", 'symmetrical': 'False', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'is_active': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'is_staff': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'is_superuser': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'last_login': ('django.db.models.fields.DateTimeField', [], {'default': 'datetime.datetime.now'}),
            'last_name': ('django.db.models.fields.CharField', [], {'max_length': '30', 'blank': 'True'}),
            'password': ('django.db.models.fields.CharField', [], {'max_length': '128'}),
            'user_permissions': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['auth.Permission']", 'symmetrical': 'False', 'blank': 'True'}),
            'username': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '30'})
        },
        'contenttypes.contenttype': {
            'Meta': {'ordering': "('name',)", 'unique_together': "(('app_label', 'model'),)", 'object_name': 'ContentType', 'db_table': "'django_content_type'"},
            'app_label': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'model': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'name': ('django.db.models.fields.CharField', [], {'max_length': '100'})
        },
        'matrr.account': {
            'Meta': {'object_name': 'Account', 'db_table': "'act_account'"},
            'act_address1': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'act_address2': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'act_city': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'act_country': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'act_fedex': ('django.db.models.fields.CharField', [], {'max_length': '9', 'null': 'True', 'blank': 'True'}),
            'act_shipping_name': ('django.db.models.fields.CharField', [], {'max_length': '25', 'null': 'True', 'blank': 'True'}),
            'act_state': ('django.db.models.fields.CharField', [], {'max_length': '2', 'null': 'True', 'blank': 'True'}),
            'act_zip': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'account'", 'unique': 'True', 'primary_key': 'True', 'db_column': "'usr_usr_id'", 'to': "orm['auth.User']"})
        },
        'matrr.bloodandgenetic': {
            'Meta': {'object_name': 'BloodAndGenetic', 'db_table': "'bag_blood_and_genetics'"},
            'bag_count_per_monkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'bag_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'bag_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'bag_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'unavailable_list': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'unavailable_blood_and_genetics_set'", 'symmetrical': 'False', 'db_table': "'bgu_blood_and_genetics_unavailable'", 'to': "orm['matrr.Monkey']"})
        },
        'matrr.bloodandgeneticrequest': {
            'Meta': {'unique_together': "(('req_request', 'blood_genetic_item'),)", 'object_name': 'BloodAndGeneticRequest', 'db_table': "'rbg_requests_to_blood_and_genetics'"},
            'blood_genetic_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blood_and_genetic_request_set'", 'db_column': "'bag_id'", 'to': "orm['matrr.BloodAndGenetic']"}),
            'monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['matrr.Monkey']", 'db_table': "'mgr_monkeys_to_blood_and_genetic_requests'", 'symmetrical': 'False'}),
            'rbg_amount': ('django.db.models.fields.FloatField', [], {}),
            'rbg_fix_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'rbg_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rbg_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'req_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blood_and_genetic_request_set'", 'db_column': "'req_request_id'", 'to': "orm['matrr.Request']"}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'unt_unit_id'", 'to': "orm['matrr.Unit']"})
        },
        'matrr.bloodandgeneticrequestreview': {
            'Meta': {'unique_together': "(('review', 'blood_and_genetic_request'),)", 'object_name': 'BloodAndGeneticRequestReview', 'db_table': "'vbg_reviews_to_blood_and_genetic_requests'"},
            'blood_and_genetic_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blood_and_genetic_request_review_set'", 'db_column': "'rbg_id'", 'to': "orm['matrr.BloodAndGeneticRequest']"}),
            'review': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blood_and_genetic_request_review_set'", 'db_column': "'rvs_review_id'", 'to': "orm['matrr.Review']"}),
            'vbg_blood_genetic_request_review_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vbg_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'vbg_priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vbg_quantity': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vbg_scientific_merit': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        },
        'matrr.bloodandgeneticrequestreviewrevision': {
            'Meta': {'unique_together': "(('review_revision', 'blood_and_genetic_request_revision'),)", 'object_name': 'BloodAndGeneticRequestReviewRevision', 'db_table': "'vgv_reviews_to_blood_and_genetic_request_revisions'"},
            'blood_and_genetic_request_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blood_genetic_request_review_revision_set'", 'db_column': "'mrv_id'", 'to': "orm['matrr.BloodAndGeneticRequestRevision']"}),
            'review_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blood_genetic_request_review_revision_set'", 'db_column': "'rvr_revision_id'", 'to': "orm['matrr.ReviewRevision']"}),
            'vgv_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'vgv_priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vgv_quantity': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vgv_review_revision_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vgv_scientific_merit': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        },
        'matrr.bloodandgeneticrequestrevision': {
            'Meta': {'unique_together': "(('request_revision', 'blood_genetic_item'),)", 'object_name': 'BloodAndGeneticRequestRevision', 'db_table': "'grr_requests_to_blood_and_genetic_revisions'"},
            'blood_genetic_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blood_and_genetic_request_revision_set'", 'db_column': "'bag_id'", 'to': "orm['matrr.BloodAndGenetic']"}),
            'grr_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'grr_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['matrr.Monkey']", 'db_table': "'mgv_monkeys_to_blood_genetic_request_revisions'", 'symmetrical': 'False'}),
            'request_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blood_and_genetic_request_revision_set'", 'db_column': "'rqv_request_revision_id'", 'to': "orm['matrr.RequestRevision']"})
        },
        'matrr.bloodandgeneticssample': {
            'Meta': {'ordering': "['bgs_deleted', 'monkey__mky_real_id', '-blood_genetic_item__bag_name']", 'object_name': 'BloodAndGeneticsSample', 'db_table': "'bgs_blood_and_genetics_samples'"},
            'bgs_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bgs_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'bgs_location': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'bgs_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'blood_genetic_item': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blood_genetic_sample_set'", 'db_column': "'bag_id'", 'to': "orm['matrr.BloodAndGenetic']"}),
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'blood_genetic_sample_set'", 'db_column': "'mky_id'", 'to': "orm['matrr.Monkey']"})
        },
        'matrr.brainblock': {
            'Meta': {'object_name': 'BrainBlock', 'db_table': "'bbl_brain_blocks'"},
            'bbl_block_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'bbl_block_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'bbl_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'})
        },
        'matrr.brainblocksample': {
            'Meta': {'ordering': "['bbs_deleted', '-monkey__mky_real_id', '-brain_block__bbl_block_name']", 'object_name': 'BrainBlockSample', 'db_table': "'bbs_brain_block_samples'"},
            'bbs_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bbs_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'bbs_location': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'bbs_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'brain_block': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'block_sample_set'", 'db_column': "'bbl_block_id'", 'to': "orm['matrr.BrainBlock']"}),
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'block_sample_set'", 'db_column': "'mky_id'", 'to': "orm['matrr.Monkey']"})
        },
        'matrr.brainregion': {
            'Meta': {'object_name': 'BrainRegion', 'db_table': "'bre_brain_regions'"},
            'bre_count_per_monkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'bre_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'bre_region_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'bre_region_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'unavailable_list': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'unavailable_brain_region_set'", 'symmetrical': 'False', 'db_table': "'bru_brain_regions_unavailable'", 'to': "orm['matrr.Monkey']"})
        },
        'matrr.brainregionrequest': {
            'Meta': {'unique_together': "(('req_request', 'brain_region'),)", 'object_name': 'BrainRegionRequest', 'db_table': "'rbr_requests_to_brain_regions'"},
            'brain_region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brain_region_request_set'", 'db_column': "'bre_region_id'", 'to': "orm['matrr.BrainRegion']"}),
            'monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['matrr.Monkey']", 'db_table': "'mbr_monkeys_to_brain_region_requests'", 'symmetrical': 'False'}),
            'rbr_fix_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'rbr_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'rbr_region_request_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'req_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brain_region_request_set'", 'db_column': "'req_request_id'", 'to': "orm['matrr.Request']"})
        },
        'matrr.brainregionrequestreview': {
            'Meta': {'unique_together': "(('review', 'brain_region_request'),)", 'object_name': 'BrainRegionRequestReview', 'db_table': "'vbr_reviews_to_brain_region_requests'"},
            'brain_region_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brain_region_request_review_set'", 'db_column': "'rbr_region_request_id'", 'to': "orm['matrr.BrainRegionRequest']"}),
            'review': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brain_region_request_review_set'", 'db_column': "'rvs_review_id'", 'to': "orm['matrr.Review']"}),
            'vbr_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'vbr_priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vbr_quantity': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vbr_region_request_review_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vbr_scientific_merit': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        },
        'matrr.brainregionrequestreviewrevision': {
            'Meta': {'unique_together': "(('review_revision', 'brain_region_request_revision'),)", 'object_name': 'BrainRegionRequestReviewRevision', 'db_table': "'vrv_reviews_to_brain_region_request_revisions'"},
            'brain_region_request_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brain_region_request_review_revision_set'", 'db_column': "'rbv_revision_id'", 'to': "orm['matrr.BrainRegionRequestRevision']"}),
            'review_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brain_region_request_review_revision_set'", 'db_column': "'rvr_revision_id'", 'to': "orm['matrr.ReviewRevision']"}),
            'vrv_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'vrv_priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vrv_quantity': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vrv_review_revision_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vrv_scientific_merit': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        },
        'matrr.brainregionrequestrevision': {
            'Meta': {'unique_together': "(('request_revision', 'brain_region'),)", 'object_name': 'BrainRegionRequestRevision', 'db_table': "'rbv_requests_to_brain_regions_revisions'"},
            'brain_region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brain_region_request_revision_set'", 'db_column': "'bbl_block_id'", 'to': "orm['matrr.BrainRegion']"}),
            'brv_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['matrr.Monkey']", 'db_table': "'mrv_monkeys_to_brain_region_request_revisions'", 'symmetrical': 'False'}),
            'rbv_revision_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'request_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'brain_region_request_revision_set'", 'db_column': "'rqv_request_revision_id'", 'to': "orm['matrr.RequestRevision']"})
        },
        'matrr.brainregionsample': {
            'Meta': {'ordering': "['brs_deleted', '-monkey__mky_real_id', '-brain_region__bre_region_name']", 'object_name': 'BrainRegionSample', 'db_table': "'brs_brain_region_samples'"},
            'brain_region': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'region_sample_set'", 'db_column': "'bre_region_id'", 'to': "orm['matrr.BrainRegion']"}),
            'brs_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'brs_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'brs_location': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'brs_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'region_sample_set'", 'db_column': "'mky_id'", 'to': "orm['matrr.Monkey']"})
        },
        'matrr.cohort': {
            'Meta': {'object_name': 'Cohort', 'db_table': "'coh_cohorts'"},
            'coh_cohort_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'coh_cohort_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'coh_species': ('django.db.models.fields.CharField', [], {'max_length': '30'}),
            'coh_upcoming': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'events': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'cohort_set'", 'symmetrical': 'False', 'through': "orm['matrr.CohortEvent']", 'to': "orm['matrr.EventType']"}),
            'institution': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cohort_set'", 'db_column': "'ins_institution_id'", 'to': "orm['matrr.Institution']"})
        },
        'matrr.cohortevent': {
            'Meta': {'object_name': 'CohortEvent', 'db_table': "'cev_cohort_events'"},
            'cev_date': ('django.db.models.fields.DateField', [], {}),
            'cev_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'cev_info': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True', 'blank': 'True'}),
            'cohort': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cohort_event_set'", 'db_column': "'coh_cohort_id'", 'to': "orm['matrr.Cohort']"}),
            'event': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cohort_event_set'", 'db_column': "'evt_id'", 'to': "orm['matrr.EventType']"})
        },
        'matrr.customtissuerequest': {
            'Meta': {'object_name': 'CustomTissueRequest', 'db_table': "'ctr_custom_tissue_requests'"},
            'ctr_amount': ('django.db.models.fields.FloatField', [], {}),
            'ctr_description': ('django.db.models.fields.TextField', [], {}),
            'ctr_fix_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'ctr_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['matrr.Monkey']", 'db_table': "'mcr_monkeys_to_custom_tissue_requests'", 'symmetrical': 'False'}),
            'req_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'custom_tissue_request_set'", 'db_column': "'req_request_id'", 'to': "orm['matrr.Request']"}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'unt_unit_id'", 'to': "orm['matrr.Unit']"})
        },
        'matrr.customtissuerequestreview': {
            'Meta': {'unique_together': "(('review', 'custom_tissue_request'),)", 'object_name': 'CustomTissueRequestReview', 'db_table': "'vct_reviews_to_custom_tissue_requests'"},
            'custom_tissue_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'custom_tissue_request_review_set'", 'db_column': "'rbg_id'", 'to': "orm['matrr.CustomTissueRequest']"}),
            'review': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'custom_tissue_request_review_set'", 'db_column': "'rvs_review_id'", 'to': "orm['matrr.Review']"}),
            'vct_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'vct_priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vct_quantity': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vct_review_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vct_scientific_merit': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        },
        'matrr.drinkingexperiment': {
            'Meta': {'object_name': 'DrinkingExperiment', 'db_table': "'dex_drinking_experiments'"},
            'cohort': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cohort_drinking_experiment_set'", 'db_column': "'coh_cohort_id'", 'to': "orm['matrr.Cohort']"}),
            'dex_date': ('django.db.models.fields.DateField', [], {}),
            'dex_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'dex_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'dex_type': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['matrr.Monkey']", 'through': "orm['matrr.MonkeyToDrinkingExperiment']", 'symmetrical': 'False'})
        },
        'matrr.event': {
            'Meta': {'object_name': 'Event'},
            'date': ('django.db.models.fields.DateField', [], {}),
            'description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'matrr.eventtype': {
            'Meta': {'object_name': 'EventType', 'db_table': "'evt_event_types'"},
            'evt_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'evt_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'evt_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'matrr.institution': {
            'Meta': {'object_name': 'Institution', 'db_table': "'ins_institutions'"},
            'ins_institution_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ins_institution_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'matrr.monkey': {
            'Meta': {'object_name': 'Monkey', 'db_table': "'mky_monkeys'"},
            'cohort': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['matrr.Cohort']", 'db_column': "'coh_cohort_id'"}),
            'mky_birthdate': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'mky_drinking': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mky_gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'mky_housing_control': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mky_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mky_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'mky_necropsy_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'mky_real_id': ('django.db.models.fields.IntegerField', [], {'unique': 'True'}),
            'mky_stress_model': ('django.db.models.fields.CharField', [], {'max_length': '30', 'null': 'True', 'blank': 'True'}),
            'mky_study_complete': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mky_weight': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'matrr.monkeytodrinkingexperiment': {
            'Meta': {'object_name': 'MonkeyToDrinkingExperiment', 'db_table': "'mtd_monkeys_to_drinking_experiments'"},
            'drinking_experiment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'dex_id'", 'to': "orm['matrr.DrinkingExperiment']"}),
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'mky_id'", 'to': "orm['matrr.Monkey']"}),
            'mtd_etoh_intake': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtd_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_total_pellets': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_veh_intake': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_weight': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'})
        },
        'matrr.mta': {
            'Meta': {'object_name': 'Mta', 'db_table': "'mta_material_transfer'"},
            'mta_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'mta_file': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '100'}),
            'mta_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mta_title': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'mta_set'", 'blank': 'True', 'db_column': "'usr_id'", 'to': "orm['auth.User']"})
        },
        'matrr.othertissuesample': {
            'Meta': {'ordering': "['ots_deleted', '-monkey__mky_real_id', '-ots_description']", 'object_name': 'OtherTissueSample', 'db_table': "'ots_other_tissue_samples'"},
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'other_sample_set'", 'db_column': "'mky_id'", 'to': "orm['matrr.Monkey']"}),
            'ots_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'ots_description': ('django.db.models.fields.TextField', [], {}),
            'ots_location': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'ots_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'})
        },
        'matrr.peripheraltissuesample': {
            'Meta': {'ordering': "['pts_deleted', '-monkey__mky_real_id', '-tissue_type__tst_tissue_name']", 'object_name': 'PeripheralTissueSample', 'db_table': "'pts_peripheral_tissue_samples'"},
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'peripheral_sample_set'", 'db_column': "'mky_id'", 'to': "orm['matrr.Monkey']"}),
            'pts_deleted': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'pts_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'pts_location': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'pts_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'tissue_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'peripheral_sample_set'", 'db_column': "'tst_type_id'", 'to': "orm['matrr.TissueType']"})
        },
        'matrr.request': {
            'Meta': {'object_name': 'Request', 'db_table': "'req_requests'"},
            'cohort': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['matrr.Cohort']", 'db_column': "'coh_cohort_id'"}),
            'req_experimental_plan': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'req_modified_date': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'req_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'req_progress_agreement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'req_project_title': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'req_reason': ('django.db.models.fields.TextField', [], {}),
            'req_referred_by': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'req_request_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'req_request_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'request_status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['matrr.RequestStatus']", 'db_column': "'rqs_status_id'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'db_column': "'usr_user_id'"})
        },
        'matrr.requestrevision': {
            'Meta': {'unique_together': "(('req_request', 'rqv_version_number'),)", 'object_name': 'RequestRevision', 'db_table': "'rqv_request_revisions'"},
            'req_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'request_revision_set'", 'db_column': "'req_request_id'", 'to': "orm['matrr.Request']"}),
            'rqv_experimental_plan': ('django.db.models.fields.files.FileField', [], {'max_length': '100'}),
            'rqv_notes': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rqv_request_date': ('django.db.models.fields.DateTimeField', [], {}),
            'rqv_request_revision_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rqv_version_number': ('django.db.models.fields.IntegerField', [], {})
        },
        'matrr.requeststatus': {
            'Meta': {'object_name': 'RequestStatus', 'db_table': "'rqs_request_statuses'"},
            'rqs_status_description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rqs_status_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rqs_status_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'matrr.review': {
            'Meta': {'unique_together': "(('user', 'req_request'),)", 'object_name': 'Review', 'db_table': "'rvs_reviews'"},
            'req_request': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['matrr.Request']", 'db_column': "'req_request_id'"}),
            'rvs_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'rvs_review_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'db_column': "'usr_user_id'"})
        },
        'matrr.reviewrevision': {
            'Meta': {'unique_together': "(('review', 'request_revision'),)", 'object_name': 'ReviewRevision', 'db_table': "'rvr_review_revisions'"},
            'request_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'review_revision_set'", 'db_column': "'rqv_request_revision_id'", 'to': "orm['matrr.RequestRevision']"}),
            'review': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'review_revision_set'", 'db_column': "'rvs_review_id'", 'to': "orm['matrr.Review']"}),
            'rvr_notes': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rvr_revision_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
        },
        'matrr.shipment': {
            'Meta': {'object_name': 'Shipment', 'db_table': "'shp_shipments'"},
            'req_request': ('django.db.models.fields.related.OneToOneField', [], {'related_name': "'shipment'", 'unique': 'True', 'to': "orm['matrr.Request']"}),
            'shp_shipment_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'shp_shipment_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'shp_tracking': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'shipment_set'", 'to': "orm['auth.User']"})
        },
        'matrr.tissuerequest': {
            'Meta': {'unique_together': "(('req_request', 'tissue_type', 'rtt_fix_type'),)", 'object_name': 'TissueRequest', 'db_table': "'rtt_requests_to_tissue_types'"},
            'monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['matrr.Monkey']", 'db_table': "'mtr_monkeys_to_tissue_requests'", 'symmetrical': 'False'}),
            'req_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_request_set'", 'db_column': "'req_request_id'", 'to': "orm['matrr.Request']"}),
            'rtt_amount': ('django.db.models.fields.FloatField', [], {}),
            'rtt_fix_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'rtt_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'rtt_tissue_request_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tissue_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_request_set'", 'db_column': "'tst_type_id'", 'to': "orm['matrr.TissueType']"}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'unt_unit_id'", 'to': "orm['matrr.Unit']"})
        },
        'matrr.tissuerequestreview': {
            'Meta': {'unique_together': "(('review', 'tissue_request'),)", 'object_name': 'TissueRequestReview', 'db_table': "'vtr_reviews_to_tissue_requests'"},
            'review': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_request_review_set'", 'db_column': "'rvs_review_id'", 'to': "orm['matrr.Review']"}),
            'tissue_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_request_review_set'", 'db_column': "'rtt_tissue_request_id'", 'to': "orm['matrr.TissueRequest']"}),
            'vtr_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'vtr_priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vtr_quantity': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vtr_request_review_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vtr_scientific_merit': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        },
        'matrr.tissuerequestreviewrevision': {
            'Meta': {'unique_together': "(('review_revision', 'tissue_request_revision'),)", 'object_name': 'TissueRequestReviewRevision', 'db_table': "'vtv_reviews_to_tissue_request_revisions'"},
            'review_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_request_review_revision_set'", 'db_column': "'rvr_revision_id'", 'to': "orm['matrr.ReviewRevision']"}),
            'tissue_request_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_request_review_revision_set'", 'db_column': "'rtv_tissue_request_id'", 'to': "orm['matrr.TissueRequestRevision']"}),
            'vtv_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'vtv_priority': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vtv_quantity': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'}),
            'vtv_review_revision_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vtv_scientific_merit': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        },
        'matrr.tissuerequestrevision': {
            'Meta': {'object_name': 'TissueRequestRevision', 'db_table': "'rtv_request_to_tissue_type_revisions'"},
            'monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['matrr.Monkey']", 'db_table': "'mtv_monkeys_to_tissue_request_revisions'", 'symmetrical': 'False'}),
            'request_revision': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_request_revision_set'", 'db_column': "'rqv_request_revision_id'", 'to': "orm['matrr.RequestRevision']"}),
            'rtv_amount': ('django.db.models.fields.FloatField', [], {}),
            'rtv_fix_type': ('django.db.models.fields.CharField', [], {'max_length': '200'}),
            'rtv_notes': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rtv_tissue_request_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tissue_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_request_revision_set'", 'db_column': "'tst_type_id'", 'to': "orm['matrr.TissueType']"}),
            'unit': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'unt_unit_id'", 'to': "orm['matrr.Unit']"})
        },
        'matrr.tissuetype': {
            'Meta': {'object_name': 'TissueType', 'db_table': "'tst_tissue_types'"},
            'tst_count_per_monkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'tst_description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'tst_tissue_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'tst_type_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unavailable_list': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'unavailable_tissue_type_set'", 'symmetrical': 'False', 'db_table': "'ttu_tissue_types_unavailable'", 'to': "orm['matrr.Monkey']"})
        },
        'matrr.unit': {
            'Meta': {'object_name': 'Unit', 'db_table': "'unt_units'"},
            'unt_unit_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unt_unit_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['matrr']
