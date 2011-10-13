# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Removing unique constraint on 'TissueType', fields ['tst_tissue_name']
        db.delete_unique('tst_tissue_types', ['tst_tissue_name'])

        # Removing unique constraint on 'TissueRequest', fields ['tissue_type', 'req_request', 'rtt_fix_type']
        db.delete_unique('rtt_requests_to_tissue_types', ['tst_type_id', 'req_request_id', 'rtt_fix_type'])

        # Removing unique constraint on 'BrainRegion', fields ['bre_region_name', 'bre_in_tube']
        db.delete_unique('bre_brain_regions', ['bre_region_name', 'bre_in_tube'])

        # Removing unique constraint on 'BrainRegionRequest', fields ['req_request', 'brain_region']
        db.delete_unique('rbr_requests_to_brain_regions', ['req_request_id', 'bre_region_id'])

        # Removing unique constraint on 'BrainRegionRequestReview', fields ['review', 'brain_region_request']
        db.delete_unique('vbr_reviews_to_brain_region_requests', ['rvs_review_id', 'rbr_region_request_id'])

        # Removing unique constraint on 'CustomTissueRequestReview', fields ['review', 'custom_tissue_request']
        db.delete_unique('vct_reviews_to_custom_tissue_requests', ['rvs_review_id', 'rbg_id'])

        # Deleting model 'CustomTissueRequestReview'
        db.delete_table('vct_reviews_to_custom_tissue_requests')

        # Deleting model 'BrainBlockSample'
        db.delete_table('bbs_brain_block_samples')

        # Deleting model 'OtherTissueSample'
        db.delete_table('ots_other_tissue_samples')

        # Deleting model 'BrainRegionSample'
        db.delete_table('brs_brain_region_samples')

        # Deleting model 'CustomTissueRequest'
        db.delete_table('ctr_custom_tissue_requests')

        # Removing M2M table for field accepted_monkeys on 'CustomTissueRequest'
        db.delete_table('acr_accepted_monkeys_to_custom_tissue_requests')

        # Removing M2M table for field monkeys on 'CustomTissueRequest'
        db.delete_table('mcr_monkeys_to_custom_tissue_requests')

        # Deleting model 'BrainBlock'
        db.delete_table('bbl_brain_blocks')

        # Deleting model 'BrainRegionRequestReview'
        db.delete_table('vbr_reviews_to_brain_region_requests')

        # Deleting model 'BrainRegionRequest'
        db.delete_table('rbr_requests_to_brain_regions')

        # Removing M2M table for field accepted_monkeys on 'BrainRegionRequest'
        db.delete_table('abr_accepted_monkeys_to_brain_region_requests')

        # Removing M2M table for field monkeys on 'BrainRegionRequest'
        db.delete_table('mbr_monkeys_to_brain_region_requests')

        # Deleting model 'BrainRegion'
        db.delete_table('bre_brain_regions')

        # Removing M2M table for field unavailable_list on 'BrainRegion'
        db.delete_table('bru_brain_regions_unavailable')

        # Deleting model 'PeripheralTissueSample'
        db.delete_table('pts_peripheral_tissue_samples')

        # Adding model 'TissueSample'
        db.create_table('tss_tissue_samples', (
            ('tss_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('tissue_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tissue_sample_set', db_column='tst_type_id', to=orm['matrr.TissueType'])),
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='tissue_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('tss_freezer', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('tss_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('tss_details', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('tss_sample_count', self.gf('django.db.models.fields.IntegerField')()),
            ('tss_distributed_count', self.gf('django.db.models.fields.IntegerField')(default=0)),
            ('tss_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['TissueSample'])

        # Adding model 'TissueCategory'
        db.create_table('cat_tissue_categories', (
            ('cat_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('cat_name', self.gf('django.db.models.fields.CharField')(unique=True, max_length=100)),
            ('cat_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('parent_category', self.gf('django.db.models.fields.related.ForeignKey')(default=None, to=orm['matrr.TissueCategory'], null=True, blank=True)),
            ('cat_internal', self.gf('django.db.models.fields.BooleanField')(default=True)),
        ))
        db.send_create_signal('matrr', ['TissueCategory'])

        # Adding field 'TissueRequest.rtt_custom_increment'
        db.add_column('rtt_requests_to_tissue_types', 'rtt_custom_increment', self.gf('django.db.models.fields.IntegerField')(default=0), keep_default=False)

        # Adding unique constraint on 'TissueRequest', fields ['tissue_type', 'req_request', 'rtt_custom_increment', 'rtt_fix_type']
        db.create_unique('rtt_requests_to_tissue_types', ['tst_type_id', 'req_request_id', 'rtt_custom_increment', 'rtt_fix_type'])

        # Deleting field 'Monkey.mky_necropsy_date'
        db.delete_column('mky_monkeys', 'mky_necropsy_date')

        # Adding field 'Monkey.mky_necropsy_start_date'
        db.add_column('mky_monkeys', 'mky_necropsy_start_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Monkey.mky_necropsy_start_date_comments'
        db.add_column('mky_monkeys', 'mky_necropsy_start_date_comments', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Monkey.mky_necropsy_end_date'
        db.add_column('mky_monkeys', 'mky_necropsy_end_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Adding field 'Monkey.mky_necropsy_end_date_comments'
        db.add_column('mky_monkeys', 'mky_necropsy_end_date_comments', self.gf('django.db.models.fields.TextField')(null=True, blank=True), keep_default=False)

        # Adding field 'Monkey.mky_age_at_necropsy'
        db.add_column('mky_monkeys', 'mky_age_at_necropsy', self.gf('django.db.models.fields.CharField')(max_length=100, null=True, blank=True), keep_default=False)

        # Adding field 'TissueType.category'
        db.add_column('tst_tissue_types', 'category', self.gf('django.db.models.fields.related.ForeignKey')(default=1, to=orm['matrr.TissueCategory'], db_column='cat_id'), keep_default=False)

        # Adding field 'TissueType.tst_cost'
        db.add_column('tst_tissue_types', 'tst_cost', self.gf('django.db.models.fields.FloatField')(default=0.0), keep_default=False)

        # Adding unique constraint on 'TissueType', fields ['category', 'tst_tissue_name']
        db.create_unique('tst_tissue_types', ['cat_id', 'tst_tissue_name'])


    def backwards(self, orm):
        
        # Removing unique constraint on 'TissueType', fields ['category', 'tst_tissue_name']
        db.delete_unique('tst_tissue_types', ['cat_id', 'tst_tissue_name'])

        # Removing unique constraint on 'TissueRequest', fields ['tissue_type', 'req_request', 'rtt_custom_increment', 'rtt_fix_type']
        db.delete_unique('rtt_requests_to_tissue_types', ['tst_type_id', 'req_request_id', 'rtt_custom_increment', 'rtt_fix_type'])

        # Adding model 'CustomTissueRequestReview'
        db.create_table('vct_reviews_to_custom_tissue_requests', (
            ('vct_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('vct_quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vct_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('custom_tissue_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='custom_tissue_request_review_set', db_column='rbg_id', to=orm['matrr.CustomTissueRequest'])),
            ('vct_scientific_merit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('review', self.gf('django.db.models.fields.related.ForeignKey')(related_name='custom_tissue_request_review_set', db_column='rvs_review_id', to=orm['matrr.Review'])),
            ('vct_review_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('matrr', ['CustomTissueRequestReview'])

        # Adding unique constraint on 'CustomTissueRequestReview', fields ['review', 'custom_tissue_request']
        db.create_unique('vct_reviews_to_custom_tissue_requests', ['rvs_review_id', 'rbg_id'])

        # Adding model 'BrainBlockSample'
        db.create_table('bbs_brain_block_samples', (
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='block_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('bbs_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('brain_block', self.gf('django.db.models.fields.related.ForeignKey')(related_name='block_sample_set', db_column='bbl_block_id', to=orm['matrr.BrainBlock'])),
            ('bbs_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('bbs_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('bbs_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('matrr', ['BrainBlockSample'])

        # Adding model 'OtherTissueSample'
        db.create_table('ots_other_tissue_samples', (
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='other_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('ots_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('ots_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('ots_description', self.gf('django.db.models.fields.TextField')()),
            ('id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ots_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
        ))
        db.send_create_signal('matrr', ['OtherTissueSample'])

        # Adding model 'BrainRegionSample'
        db.create_table('brs_brain_region_samples', (
            ('brs_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='region_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('brs_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('brain_region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='region_sample_set', db_column='bre_region_id', to=orm['matrr.BrainRegion'])),
            ('brs_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('brs_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
        ))
        db.send_create_signal('matrr', ['BrainRegionSample'])

        # Adding model 'CustomTissueRequest'
        db.create_table('ctr_custom_tissue_requests', (
            ('ctr_fix_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('ctr_description', self.gf('django.db.models.fields.TextField')()),
            ('unit', self.gf('django.db.models.fields.related.ForeignKey')(related_name='+', db_column='unt_unit_id', to=orm['matrr.Unit'])),
            ('ctr_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('ctr_amount', self.gf('django.db.models.fields.FloatField')()),
            ('req_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='custom_tissue_request_set', db_column='req_request_id', to=orm['matrr.Request'])),
        ))
        db.send_create_signal('matrr', ['CustomTissueRequest'])

        # Adding M2M table for field accepted_monkeys on 'CustomTissueRequest'
        db.create_table('acr_accepted_monkeys_to_custom_tissue_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('customtissuerequest', models.ForeignKey(orm['matrr.customtissuerequest'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('acr_accepted_monkeys_to_custom_tissue_requests', ['customtissuerequest_id', 'monkey_id'])

        # Adding M2M table for field monkeys on 'CustomTissueRequest'
        db.create_table('mcr_monkeys_to_custom_tissue_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('customtissuerequest', models.ForeignKey(orm['matrr.customtissuerequest'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('mcr_monkeys_to_custom_tissue_requests', ['customtissuerequest_id', 'monkey_id'])

        # Adding model 'BrainBlock'
        db.create_table('bbl_brain_blocks', (
            ('bbl_block_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bbl_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('bbl_block_name', self.gf('django.db.models.fields.CharField')(max_length=100, unique=True)),
        ))
        db.send_create_signal('matrr', ['BrainBlock'])

        # Adding model 'BrainRegionRequestReview'
        db.create_table('vbr_reviews_to_brain_region_requests', (
            ('vbr_scientific_merit', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vbr_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('vbr_quantity', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
            ('vbr_region_request_review_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('brain_region_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_review_set', db_column='rbr_region_request_id', to=orm['matrr.BrainRegionRequest'])),
            ('review', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_review_set', db_column='rvs_review_id', to=orm['matrr.Review'])),
            ('vbr_priority', self.gf('django.db.models.fields.PositiveSmallIntegerField')(null=True)),
        ))
        db.send_create_signal('matrr', ['BrainRegionRequestReview'])

        # Adding unique constraint on 'BrainRegionRequestReview', fields ['review', 'brain_region_request']
        db.create_unique('vbr_reviews_to_brain_region_requests', ['rvs_review_id', 'rbr_region_request_id'])

        # Adding model 'BrainRegionRequest'
        db.create_table('rbr_requests_to_brain_regions', (
            ('rbr_region_request_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('rbr_fix_type', self.gf('django.db.models.fields.CharField')(max_length=200)),
            ('rbr_notes', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
            ('brain_region', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_set', db_column='bre_region_id', to=orm['matrr.BrainRegion'])),
            ('req_request', self.gf('django.db.models.fields.related.ForeignKey')(related_name='brain_region_request_set', db_column='req_request_id', to=orm['matrr.Request'])),
        ))
        db.send_create_signal('matrr', ['BrainRegionRequest'])

        # Adding M2M table for field accepted_monkeys on 'BrainRegionRequest'
        db.create_table('abr_accepted_monkeys_to_brain_region_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('brainregionrequest', models.ForeignKey(orm['matrr.brainregionrequest'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('abr_accepted_monkeys_to_brain_region_requests', ['brainregionrequest_id', 'monkey_id'])

        # Adding M2M table for field monkeys on 'BrainRegionRequest'
        db.create_table('mbr_monkeys_to_brain_region_requests', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('brainregionrequest', models.ForeignKey(orm['matrr.brainregionrequest'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('mbr_monkeys_to_brain_region_requests', ['brainregionrequest_id', 'monkey_id'])

        # Adding unique constraint on 'BrainRegionRequest', fields ['req_request', 'brain_region']
        db.create_unique('rbr_requests_to_brain_regions', ['req_request_id', 'bre_region_id'])

        # Adding model 'BrainRegion'
        db.create_table('bre_brain_regions', (
            ('bre_count_per_monkey', self.gf('django.db.models.fields.IntegerField')(null=True, blank=True)),
            ('bre_region_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('bre_in_tube', self.gf('django.db.models.fields.BooleanField')(default=False)),
            ('bre_region_name', self.gf('django.db.models.fields.CharField')(max_length=100, unique=True)),
            ('bre_description', self.gf('django.db.models.fields.TextField')(null=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['BrainRegion'])

        # Adding M2M table for field unavailable_list on 'BrainRegion'
        db.create_table('bru_brain_regions_unavailable', (
            ('id', models.AutoField(verbose_name='ID', primary_key=True, auto_created=True)),
            ('brainregion', models.ForeignKey(orm['matrr.brainregion'], null=False)),
            ('monkey', models.ForeignKey(orm['matrr.monkey'], null=False))
        ))
        db.create_unique('bru_brain_regions_unavailable', ['brainregion_id', 'monkey_id'])

        # Adding unique constraint on 'BrainRegion', fields ['bre_region_name', 'bre_in_tube']
        db.create_unique('bre_brain_regions', ['bre_region_name', 'bre_in_tube'])

        # Adding model 'PeripheralTissueSample'
        db.create_table('pts_peripheral_tissue_samples', (
            ('tissue_type', self.gf('django.db.models.fields.related.ForeignKey')(related_name='peripheral_sample_set', db_column='tst_type_id', to=orm['matrr.TissueType'])),
            ('monkey', self.gf('django.db.models.fields.related.ForeignKey')(related_name='peripheral_sample_set', db_column='mky_id', to=orm['matrr.Monkey'])),
            ('pts_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('pts_location', self.gf('django.db.models.fields.CharField')(max_length=100)),
            ('pts_modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
            ('pts_deleted', self.gf('django.db.models.fields.BooleanField')(default=False)),
        ))
        db.send_create_signal('matrr', ['PeripheralTissueSample'])

        # Deleting model 'TissueSample'
        db.delete_table('tss_tissue_samples')

        # Deleting model 'TissueCategory'
        db.delete_table('cat_tissue_categories')

        # Deleting field 'TissueRequest.rtt_custom_increment'
        db.delete_column('rtt_requests_to_tissue_types', 'rtt_custom_increment')

        # Adding unique constraint on 'TissueRequest', fields ['tissue_type', 'req_request', 'rtt_fix_type']
        db.create_unique('rtt_requests_to_tissue_types', ['tst_type_id', 'req_request_id', 'rtt_fix_type'])

        # Adding field 'Monkey.mky_necropsy_date'
        db.add_column('mky_monkeys', 'mky_necropsy_date', self.gf('django.db.models.fields.DateField')(null=True, blank=True), keep_default=False)

        # Deleting field 'Monkey.mky_necropsy_start_date'
        db.delete_column('mky_monkeys', 'mky_necropsy_start_date')

        # Deleting field 'Monkey.mky_necropsy_start_date_comments'
        db.delete_column('mky_monkeys', 'mky_necropsy_start_date_comments')

        # Deleting field 'Monkey.mky_necropsy_end_date'
        db.delete_column('mky_monkeys', 'mky_necropsy_end_date')

        # Deleting field 'Monkey.mky_necropsy_end_date_comments'
        db.delete_column('mky_monkeys', 'mky_necropsy_end_date_comments')

        # Deleting field 'Monkey.mky_age_at_necropsy'
        db.delete_column('mky_monkeys', 'mky_age_at_necropsy')

        # Deleting field 'TissueType.category'
        db.delete_column('tst_tissue_types', 'cat_id')

        # Deleting field 'TissueType.tst_cost'
        db.delete_column('tst_tissue_types', 'tst_cost')

        # Adding unique constraint on 'TissueType', fields ['tst_tissue_name']
        db.create_unique('tst_tissue_types', ['tst_tissue_name'])


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
            'mky_age_at_necropsy': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'mky_birthdate': ('django.db.models.fields.CharField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
            'mky_drinking': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mky_gender': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'mky_housing_control': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'mky_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mky_name': ('django.db.models.fields.CharField', [], {'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'mky_necropsy_end_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'mky_necropsy_end_date_comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'mky_necropsy_start_date': ('django.db.models.fields.DateField', [], {'null': 'True', 'blank': 'True'}),
            'mky_necropsy_start_date_comments': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
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
        'matrr.tissuecategory': {
            'Meta': {'object_name': 'TissueCategory', 'db_table': "'cat_tissue_categories'"},
            'cat_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'cat_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'cat_internal': ('django.db.models.fields.BooleanField', [], {'default': 'True'}),
            'cat_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'}),
            'parent_category': ('django.db.models.fields.related.ForeignKey', [], {'default': 'None', 'to': "orm['matrr.TissueCategory']", 'null': 'True', 'blank': 'True'})
        },
        'matrr.tissuerequest': {
            'Meta': {'unique_together': "(('req_request', 'tissue_type', 'rtt_fix_type', 'rtt_custom_increment'),)", 'object_name': 'TissueRequest', 'db_table': "'rtt_requests_to_tissue_types'"},
            'accepted_monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'related_name': "'accepted_tissue_request_set'", 'symmetrical': 'False', 'db_table': "'atr_accepted_monkeys_to_tissue_requests'", 'to': "orm['matrr.Monkey']"}),
            'monkeys': ('django.db.models.fields.related.ManyToManyField', [], {'to': "orm['matrr.Monkey']", 'db_table': "'mtr_monkeys_to_tissue_requests'", 'symmetrical': 'False'}),
            'req_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_request_set'", 'db_column': "'req_request_id'", 'to': "orm['matrr.Request']"}),
            'rtt_amount': ('django.db.models.fields.FloatField', [], {}),
            'rtt_custom_increment': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
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
        'matrr.tissuesample': {
            'Meta': {'ordering': "['-monkey__mky_real_id', '-tissue_type__tst_tissue_name']", 'object_name': 'TissueSample', 'db_table': "'tss_tissue_samples'"},
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_sample_set'", 'db_column': "'mky_id'", 'to': "orm['matrr.Monkey']"}),
            'tissue_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_sample_set'", 'db_column': "'tst_type_id'", 'to': "orm['matrr.TissueType']"}),
            'tss_details': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'tss_distributed_count': ('django.db.models.fields.IntegerField', [], {'default': '0'}),
            'tss_freezer': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tss_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tss_location': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tss_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'tss_sample_count': ('django.db.models.fields.IntegerField', [], {})
        },
        'matrr.tissuetype': {
            'Meta': {'unique_together': "(('tst_tissue_name', 'category'),)", 'object_name': 'TissueType', 'db_table': "'tst_tissue_types'"},
            'category': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['matrr.TissueCategory']", 'db_column': "'cat_id'"}),
            'tst_cost': ('django.db.models.fields.FloatField', [], {'default': '0.0'}),
            'tst_count_per_monkey': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'tst_description': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'tst_tissue_name': ('django.db.models.fields.CharField', [], {'max_length': '100'}),
            'tst_type_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unavailable_list': ('django.db.models.fields.related.ManyToManyField', [], {'symmetrical': 'False', 'related_name': "'unavailable_tissue_type_set'", 'blank': 'True', 'db_table': "'ttu_tissue_types_unavailable'", 'to': "orm['matrr.Monkey']"})
        },
        'matrr.unit': {
            'Meta': {'object_name': 'Unit', 'db_table': "'unt_units'"},
            'unt_unit_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'unt_unit_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        }
    }

    complete_apps = ['matrr']
