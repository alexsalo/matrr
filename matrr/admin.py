from matrr.models import *
from django.contrib import admin

class TissueAdmin(admin.ModelAdmin):
  formfield_overrides = {
    models.ManyToManyField: {'widget': admin.widgets.FilteredSelectMultiple("Monkeys", is_stacked=False)},
  }

class PeripheralTissueSampleAdmin(admin.ModelAdmin):
  actions = ['remove_samples_from_inventory']
  
  def remove_samples_from_inventory(self, request, queryset):
    queryset.update(pts_deleted=True)
  remove_samples_from_inventory.short_description='Remove selected samples from inventory'


class BrainBlockSampleAdmin(admin.ModelAdmin):
  actions = ['remove_samples_from_inventory']

  def remove_samples_from_inventory(self, request, queryset):
    queryset.update(bbs_deleted=True)
  remove_samples_from_inventory.short_description='Remove selected samples from inventory'


class BrainRegionSampleAdmin(admin.ModelAdmin):
  actions = ['remove_samples_from_inventory']

  def remove_samples_from_inventory(self, request, queryset):
    queryset.update(brs_deleted=True)
  remove_samples_from_inventory.short_description='Remove selected samples from inventory'

class BloodGeneticsSampleAdmin(admin.ModelAdmin):
  actions = ['remove_samples_from_inventory']

  def remove_samples_from_inventory(self, request, queryset):
    queryset.update(bgs_deleted=True)
  remove_samples_from_inventory.short_description='Remove selected samples from inventory'

class OtherTissueSampleAdmin(admin.ModelAdmin):
  actions = ['remove_samples_from_inventory']

  def remove_samples_from_inventory(self, request, queryset):
    queryset.update(ots_deleted=True)
  remove_samples_from_inventory.short_description='Remove selected samples from inventory'

admin.site.register(TissueType, TissueAdmin)
admin.site.register(BrainBlock)
admin.site.register(BrainRegion, TissueAdmin)
admin.site.register(BloodAndGenetic, TissueAdmin)
admin.site.register(Cohort)
admin.site.register(CohortEvent)
admin.site.register(EventType)
admin.site.register(Monkey)
admin.site.register(RequestStatus)
admin.site.register(Unit)
admin.site.register(DrinkingExperiment)
admin.site.register(MonkeyToDrinkingExperiment)
admin.site.register(Institution)
admin.site.register(Event)
admin.site.register(PeripheralTissueSample, PeripheralTissueSampleAdmin)
admin.site.register(BrainBlockSample, BrainBlockSampleAdmin)
admin.site.register(BrainRegionSample, BrainRegionSampleAdmin)
admin.site.register(BloodAndGeneticsSample, BloodGeneticsSampleAdmin)
admin.site.register(OtherTissueSample, OtherTissueSampleAdmin)
