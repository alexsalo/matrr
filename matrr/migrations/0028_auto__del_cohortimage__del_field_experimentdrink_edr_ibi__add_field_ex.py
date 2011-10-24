# encoding: utf-8
import datetime
from south.db import db
from south.v2 import SchemaMigration
from django.db import models

class Migration(SchemaMigration):

    def forwards(self, orm):
        
        # Deleting model 'CohortImage'
        db.delete_table('cig_cohort_image')

        # Deleting field 'ExperimentDrink.edr_ibi'
        db.rename_column('edr_experiment_drinks', 'edr_ibi', 'edr_idi')

        # Adding field 'ExperimentDrink.edr_idi'
        #db.add_column('edr_experiment_drinks', 'edr_idi', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True), keep_default=False)


    def backwards(self, orm):
        
        # Adding model 'CohortImage'
        db.create_table('cig_cohort_image', (
            ('cohort', self.gf('django.db.models.fields.related.ForeignKey')(related_name='image_set', to=orm['matrr.Cohort'])),
            ('parameters', self.gf('django.db.models.fields.CharField')(max_length=500, blank=True)),
            ('cig_id', self.gf('django.db.models.fields.AutoField')(primary_key=True)),
            ('title', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('image', self.gf('django.db.models.fields.files.ImageField')(default='', max_length=100)),
            ('html_fragment', self.gf('django.db.models.fields.files.FileField')(max_length=100, null=True)),
            ('thumbnail', self.gf('django.db.models.fields.files.ImageField')(default='', max_length=100, null=True, blank=True)),
            ('method', self.gf('django.db.models.fields.CharField')(max_length=50, blank=True)),
            ('modified', self.gf('django.db.models.fields.DateTimeField')(auto_now=True, auto_now_add=True, blank=True)),
        ))
        db.send_create_signal('matrr', ['CohortImage'])

        # Adding field 'ExperimentDrink.edr_ibi'
        db.add_column('edr_experiment_drinks', 'edr_ibi', self.gf('django.db.models.fields.PositiveIntegerField')(null=True, blank=True), keep_default=False)

        # Deleting field 'ExperimentDrink.edr_idi'
        db.delete_column('edr_experiment_drinks', 'edr_idi')


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
        'matrr.cohortdata': {
            'Meta': {'object_name': 'CohortData', 'db_table': "'cod_cohort_datafile'"},
            'cod_file': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '100'}),
            'cod_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'cod_title': ('django.db.models.fields.CharField', [], {'max_length': '35', 'blank': 'True'}),
            'cohort': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'cod_set'", 'db_column': "'coh_cohort_id'", 'to': "orm['matrr.Cohort']"})
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
        'matrr.experimentbout': {
            'Meta': {'object_name': 'ExperimentBout', 'db_table': "'ebt_experiment_bouts'"},
            'ebt_end_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'ebt_ibi': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'ebt_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'ebt_length': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'ebt_number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'ebt_start_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'ebt_volume': ('django.db.models.fields.FloatField', [], {}),
            'mtd': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'bouts_set'", 'db_column': "'mtd_id'", 'to': "orm['matrr.MonkeyToDrinkingExperiment']"})
        },
        'matrr.experimentdrink': {
            'Meta': {'object_name': 'ExperimentDrink', 'db_table': "'edr_experiment_drinks'"},
            'ebt': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'drinks_set'", 'db_column': "'ebt_id'", 'to': "orm['matrr.ExperimentBout']"}),
            'edr_end_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'edr_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'edr_idi': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'edr_length': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'edr_number': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'edr_start_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'edr_volume': ('django.db.models.fields.FloatField', [], {})
        },
        'matrr.experimentevent': {
            'Meta': {'object_name': 'ExperimentEvent', 'db_table': "'eev_experiment_events'"},
            'eev_blank': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'eev_dose': ('django.db.models.fields.FloatField', [], {}),
            'eev_etoh_bout_number': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'eev_etoh_drink_number': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'eev_etoh_elapsed_time_since_last': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'eev_etoh_side': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'eev_etoh_total': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'eev_etoh_volume': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'eev_event_type': ('django.db.models.fields.CharField', [], {'max_length': '1'}),
            'eev_experiment_state': ('django.db.models.fields.IntegerField', [], {}),
            'eev_fixed_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'eev_hand_in_bar': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'eev_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'eev_occurred': ('django.db.models.fields.DateTimeField', [], {}),
            'eev_pellet_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'eev_scale_string': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'eev_segement_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'eev_session_time': ('django.db.models.fields.PositiveIntegerField', [], {}),
            'eev_timing_comment': ('django.db.models.fields.CharField', [], {'max_length': '50', 'null': 'True', 'blank': 'True'}),
            'eev_veh_bout_number': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'eev_veh_drink_number': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'eev_veh_elapsed_time_since_last': ('django.db.models.fields.PositiveIntegerField', [], {'null': 'True', 'blank': 'True'}),
            'eev_veh_side': ('django.db.models.fields.CharField', [], {'max_length': '1', 'null': 'True', 'blank': 'True'}),
            'eev_veh_total': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'eev_veh_volume': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'events_set'", 'db_column': "'mtd_id'", 'to': "orm['matrr.MonkeyToDrinkingExperiment']"})
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
            'mky_birthdate': ('django.db.models.fields.DateField', [], {'max_length': '20', 'null': 'True', 'blank': 'True'}),
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
        'matrr.monkeyimage': {
            'Meta': {'object_name': 'MonkeyImage', 'db_table': "'mig_monkey_image'"},
            'html_fragment': ('django.db.models.fields.files.FileField', [], {'max_length': '100', 'null': 'True'}),
            'image': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100'}),
            'method': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'}),
            'mig_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'image_set'", 'to': "orm['matrr.Monkey']"}),
            'parameters': ('django.db.models.fields.CharField', [], {'default': "'defaults'", 'max_length': '500', 'blank': 'True'}),
            'thumbnail': ('django.db.models.fields.files.ImageField', [], {'default': "''", 'max_length': '100', 'null': 'True', 'blank': 'True'}),
            'title': ('django.db.models.fields.CharField', [], {'max_length': '50', 'blank': 'True'})
        },
        'matrr.monkeytodrinkingexperiment': {
            'Meta': {'object_name': 'MonkeyToDrinkingExperiment', 'db_table': "'mtd_monkeys_to_drinking_experiments'"},
            'drinking_experiment': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'dex_id'", 'to': "orm['matrr.DrinkingExperiment']"}),
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'db_column': "'mky_id'", 'to': "orm['matrr.Monkey']"}),
            'mtd_drinks_1st_bout': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_bout': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_conc': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_drink_bout': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_g_kg': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_intake': ('django.db.models.fields.FloatField', [], {}),
            'mtd_etoh_mean_bout_length': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_mean_bout_vol': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_mean_drink_length': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_mean_drink_vol': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_media_ibi': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_median_idi': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_st_1': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_st_2': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_etoh_st_3': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_fi_wo_drinking_st_1': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'mtd_latency_1st_drink': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_length_st_1': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_length_st_2': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_length_st_3': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_max_bout': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_max_bout_end': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_max_bout_length': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_max_bout_start': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_max_bout_vol': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_mean_drink_vol_1st_bout': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_notes': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_pct_etoh': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_pct_etoh_in_1st_bout': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_pct_exp_etoh': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_pct_fi_with_drinking_st_1': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_pct_max_bout_vol_total_etoh': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_pellets_st_1': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_pellets_st_3': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_st_1_ioc_avg': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_total_pellets': ('django.db.models.fields.IntegerField', [], {}),
            'mtd_veh_bout': ('django.db.models.fields.IntegerField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_veh_drink_bout': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_veh_intake': ('django.db.models.fields.FloatField', [], {}),
            'mtd_veh_st_2': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_veh_st_3': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
            'mtd_vol_1st_bout': ('django.db.models.fields.FloatField', [], {'null': 'True', 'blank': 'True'}),
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
            'req_report_asked': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'req_request_date': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'req_request_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'req_safety_agreement': ('django.db.models.fields.BooleanField', [], {'default': 'False'}),
            'request_status': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['matrr.RequestStatus']", 'db_column': "'rqs_status_id'"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'to': "orm['auth.User']", 'db_column': "'usr_user_id'"})
        },
        'matrr.requeststatus': {
            'Meta': {'object_name': 'RequestStatus', 'db_table': "'rqs_request_statuses'"},
            'rqs_status_description': ('django.db.models.fields.TextField', [], {'null': 'True'}),
            'rqs_status_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rqs_status_name': ('django.db.models.fields.CharField', [], {'unique': 'True', 'max_length': '100'})
        },
        'matrr.researchupdate': {
            'Meta': {'object_name': 'ResearchUpdate', 'db_table': "'rud_research_update'"},
            'request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'rud_set'", 'db_column': "'req_id'", 'to': "orm['matrr.Request']"}),
            'rud_date': ('django.db.models.fields.DateField', [], {'auto_now_add': 'True', 'null': 'True', 'blank': 'True'}),
            'rud_file': ('django.db.models.fields.files.FileField', [], {'default': "''", 'max_length': '100'}),
            'rud_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'rud_title': ('django.db.models.fields.CharField', [], {'max_length': '25', 'blank': 'True'})
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
        'matrr.tissueinventoryverification': {
            'Meta': {'object_name': 'TissueInventoryVerification', 'db_table': "'tiv_tissue_verification'"},
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_verification_set'", 'db_column': "'mky_id'", 'to': "orm['matrr.Monkey']"}),
            'tissue_request': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_verification_set'", 'null': 'True', 'db_column': "'rtt_tissue_request_id'", 'to': "orm['matrr.TissueRequest']"}),
            'tissue_sample': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_verification_set'", 'null': 'True', 'db_column': "'tss_id'", 'to': "orm['matrr.TissueSample']"}),
            'tissue_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_verification_set'", 'db_column': "'tst_type_id'", 'to': "orm['matrr.TissueType']"}),
            'tiv_date_created': ('django.db.models.fields.DateTimeField', [], {'auto_now_add': 'True', 'blank': 'True'}),
            'tiv_date_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'tiv_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tiv_inventory': ('django.db.models.fields.CharField', [], {'default': "'Unverified'", 'max_length': '100'}),
            'tiv_notes': ('django.db.models.fields.TextField', [], {'blank': 'True'})
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
            'vtr_quantity': ('django.db.models.fields.CharField', [], {'max_length': '12', 'null': 'True'}),
            'vtr_request_review_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'vtr_scientific_merit': ('django.db.models.fields.PositiveSmallIntegerField', [], {'null': 'True'})
        },
        'matrr.tissuesample': {
            'Meta': {'ordering': "['-monkey__mky_real_id', '-tissue_type__tst_tissue_name']", 'object_name': 'TissueSample', 'db_table': "'tss_tissue_samples'"},
            'monkey': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_sample_set'", 'db_column': "'mky_id'", 'to': "orm['matrr.Monkey']"}),
            'tissue_type': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'tissue_sample_set'", 'db_column': "'tst_type_id'", 'to': "orm['matrr.TissueType']"}),
            'tss_details': ('django.db.models.fields.TextField', [], {'null': 'True', 'blank': 'True'}),
            'tss_freezer': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'tss_id': ('django.db.models.fields.AutoField', [], {'primary_key': 'True'}),
            'tss_location': ('django.db.models.fields.CharField', [], {'max_length': '100', 'blank': 'True'}),
            'tss_modified': ('django.db.models.fields.DateTimeField', [], {'auto_now': 'True', 'auto_now_add': 'True', 'blank': 'True'}),
            'tss_sample_quantity': ('django.db.models.fields.FloatField', [], {'default': '0', 'null': 'True'}),
            'units': ('django.db.models.fields.related.ForeignKey', [], {'default': '4', 'to': "orm['matrr.Unit']"}),
            'user': ('django.db.models.fields.related.ForeignKey', [], {'related_name': "'+'", 'null': 'True', 'db_column': "'usr_usr_id'", 'to': "orm['auth.User']"})
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
