# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'BloodAndGeneticRequest', fields ['req_request', 'blood_genetic_item']
        db.delete_unique('rbg_requests_to_blood_and_genetics', ['req_request_id', 'bag_id'])

        # Removing unique constraint on 'BloodAndGeneticRequestReview', fields ['review', 'blood_and_genetic_request']
        db.delete_unique('vbg_reviews_to_blood_and_genetic_requests', ['rvs_review_id', 'rbg_id'])

        # Deleting model 'BloodAndGeneticRequestReview'
        db.delete_table('vbg_reviews_to_blood_and_genetic_requests')

        # Deleting model 'BloodAndGeneticRequest'
        db.delete_table('rbg_requests_to_blood_and_genetics')

        # Removing M2M table for field accepted_monkeys on 'BloodAndGeneticRequest'
        db.delete_table('agr_accepted_monkeys_to_blood_and_genetic_requests')

        # Removing M2M table for field monkeys on 'BloodAndGeneticRequest'
        db.delete_table('mgr_monkeys_to_blood_and_genetic_requests')

        # Deleting model 'BloodAndGenetic'
        db.delete_table('bag_blood_and_genetics')

        # Removing M2M table for field unavailable_list on 'BloodAndGenetic'
        db.delete_table('bgu_blood_and_genetics_unavailable')

        # Deleting model 'BloodAndGeneticsSample'
        db.delete_table('bgs_blood_and_genetics_samples')

        # Adding field 'BrainRegion.bre_in_tube'
        db.add_column('bre_brain_regions', 'bre_in_tube', self.gf('django.db.models.fields.BooleanField')(default=False), keep_default=False)

        # Adding unique constraint on 'BrainRegion', fields ['bre_in_tube', 'bre_region_name']
        db.create_unique('bre_brain_regions', ['bre_in_tube', 'bre_region_name'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'BrainRegion', fields ['bre_in_tube', 'bre_region_name']
        db.delete_unique('bre_brain_regions', ['bre_in_tube', 'bre_region_name'])

        # Adding model 'BloodAndGeneticRequestReview'
        db.create_table('vbg_reviews_to_blood_and_genetic_requests', (
            ('vbg_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('blood_and_genetic_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_and_genetic_request_review_set', db_column='rbg_id', to=orm['matrr.BloodAndGeneticRequest'])),
            ('vbg_quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('review', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_and_genetic_request_review_set', db_column='rvs_review_id', to=orm['matrr.Review'])),
            ('vbg_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vbg_blood_genetic_request_review_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('vbg_scientific_merit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
        ))
        db.send_create_signal('matrr', ['BloodAndGeneticRequestReview'])

        # Adding unique constraint on 'BloodAndGeneticRequestReview', fields ['review', 'blood_and_genetic_request']
        db.create_unique('vbg_reviews_to_blood_and_genetic_requests', ['rvs_review_id', 'rbg_id'])

        # Adding model 'BloodAndGeneticRequest'
        db.create_table('rbg_requests_to_blood_and_genetics', (
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='unt_unit_id', to=orm['matrr.Unit'])),
            ('rbg_amount', self.gf('django.db.models.fields.FloatField')()),
            ('blood_genetic_item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_and_genetic_request_set', db_column='bag_id', to=orm['matrr.BloodAndGenetic'])),
            ('rbg_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rbg_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('rbg_fix_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('req_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_and_genetic_request_set', db_column='req_request_id', to=orm['matrr.Request'])),
        ))
        db.send_create_signal('matrr', ['BloodAndGeneticRequest'])

        # Adding M2M table for field accepted_monkeys on 'BloodAndGeneticRequest'
        db.create_table('agr_accepted_monkeys_to_blood_and_genetic_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bloodandgeneticrequest', models.ForeignKey(orm['matrr.bloodandgeneticrequest'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('agr_accepted_monkeys_to_blood_and_genetic_requests', ['bloodandgeneticrequest_id', 'monkey_id'])

        # Adding M2M table for field monkeys on 'BloodAndGeneticRequest'
        db.create_table('mgr_monkeys_to_blood_and_genetic_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bloodandgeneticrequest', models.ForeignKey(orm['matrr.bloodandgeneticrequest'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('mgr_monkeys_to_blood_and_genetic_requests', ['bloodandgeneticrequest_id', 'monkey_id'])

        # Adding unique constraint on 'BloodAndGeneticRequest', fields ['req_request', 'blood_genetic_item']
        db.create_unique('rbg_requests_to_blood_and_genetics', ['req_request_id', 'bag_id'])

        # Adding model 'BloodAndGenetic'
        db.create_table('bag_blood_and_genetics', (
            ('bag_name', self.gf('django.db.models.fields.CharField')(max_length=100, unique=True)),
            ('bag_count_per_monkey', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('bag_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bag_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BloodAndGenetic'])

        # Adding M2M table for field unavailable_list on 'BloodAndGenetic'
        db.create_table('bgu_blood_and_genetics_unavailable', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('bloodandgenetic', models.ForeignKey(orm['matrr.bloodandgenetic'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('bgu_blood_and_genetics_unavailable', ['bloodandgenetic_id', 'monkey_id'])

        # Adding model 'BloodAndGeneticsSample'
        db.create_table('bgs_blood_and_genetics_samples', (
            ('bgs_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_genetic_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('bgs_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('blood_genetic_item', self.gf('django.db.models.fields.related.ForeignKey')(related_name='blood_genetic_sample_set', db_column='bag_id', to=orm['matrr.BloodAndGenetic'])),
            ('bgs_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('bgs_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('matrr', ['BloodAndGeneticsSample'])

        # Deleting field 'BrainRegion.bre_in_tube'
        db.delete_column('bre_brain_regions', 'bre_in_tube')


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
            'name': ('django.db.models.fields.CharField', [], {'max_length': '50'})
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
            'Meta': {'unique_together': "(('bre_region_name', 'bre_in_tube'),)", 'object_name': 'BrainRegion', 'db_table': "'bre_brain_regions'"},
            'bre_count_per_monkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'bre_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'bre_in_tube': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'bre_region_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'bre_region_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'unavailable_list': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'unavailable_brain_region_set'", 'symmetrical': 'False', 'db_table': "'bru_brain_regions_unavailable'", 'to': "orm['matrr.Monkey']"})
        },
        'matrr.brainregionrequest': {
            'Meta': {'unique_together': "(('req_request', 'brain_region'),)", 'object_name': 'BrainRegionRequest', 'db_table': "'rbr_requests_to_brain_regions'"},
            'accepted_monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'accepted_brain_region_request_set'", 'symmetrical': 'False', 'db_table': "'abr_accepted_monkeys_to_brain_region_requests'", 'to': "orm['matrr.Monkey']"}),
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
            'accepted_monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'accepted_custom_request_set'", 'symmetrical': 'False', 'db_table': "'acr_accepted_monkeys_to_custom_tissue_requests'", 'to': "orm['matrr.Monkey']"}),
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
        'matrr.genbanksequence': {
            'Meta': {'object_name': 'GenBankSequence', 'db_table': "'gen_genbank_sequences'"},
            'accession': ('django.db.models.fields.CharField', [], {'max_length': '20'}),
            'cohort': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'genbank_set'", 'symmetrical': 'False', 'db_table': "'gtc_genbank_to_cohorts'", 'to': "orm['matrr.Cohort']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'})
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
        'matrr.publication': {
            'Meta': {'object_name': 'Publication', 'db_table': "'pub_publications'"},
            'abstract': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'authors': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'cohorts': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'publication_set'", 'null': 'True', 'db_table': "'ptc_publications_to_cohorts'", 'to': "orm['matrr.Cohort']"}),
            'id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'isbn': ('django.db.models.fields.IntegerField', [], {'null': 'True'}),
            'issue': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'journal': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'keywords': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'pmcid': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'}),
            'pmid': ('django.db.models.fields.IntegerField', [], {'unique': 'True', 'null': 'True'}),
            'published_month': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'published_year': ('django.db.models.fields.CharField', [], {'max_length': '10', 'null': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '200', 'null': 'True'}),
            'volume': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True'})
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
            'accepted_monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'accepted_tissue_request_set'", 'symmetrical': 'False', 'db_table': "'atr_accepted_monkeys_to_tissue_requests'", 'to': "orm['matrr.Monkey']"}),
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
