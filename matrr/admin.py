from matrr.models import *
from django.contrib import admin
from abc import abstractmethod, abstractproperty

class TissueAdmin(admin.ModelAdmin):
  formfield_overrides = {
    models.ManyToManyField: {'widget': admin.widgets.FilteredSelectMultiple("Monkeys", is_stacked=False)},
  }


class SampleAdmin(admin.ModelAdmin):
  actions = ['remove_samples_from_inventory',
             'update_inventory_dates']
  @abstractproperty
  def readonly_fields(self):
    return None

  def update_inventory_dates(self, request, queryset):
    for model in queryset.all():
      model.save()

  @abstractmethod
  def remove_samples_from_inventory(self, request, queryset):
    return None
  remove_samples_from_inventory.short_description='Remove selected samples from inventory'

  class Meta:
    abstract = True


class PeripheralTissueSampleAdmin(SampleAdmin):
  readonly_fields = ('pts_modified',)

  def queryset(self, request):
    return PeripheralTissueSample.objects
  
  def remove_samples_from_inventory(self, request, queryset):
    queryset.update(pts_deleted=True)


class BrainBlockSampleAdmin(SampleAdmin):
  readonly_fields = ('bbs_modified',)

  def remove_samples_from_inventory(self, request, queryset):
    queryset.update(bbs_deleted=True)


class BrainRegionSampleAdmin(SampleAdmin):
  readonly_fields = ('brs_modified',)

  def remove_samples_from_inventory(self, request, queryset):
    queryset.update(brs_deleted=True)


class OtherTissueSampleAdmin(SampleAdmin):
  readonly_fields = ('ots_modified',)

  def remove_samples_from_inventory(self, request, queryset):
    queryset.update(ots_deleted=True)


admin.site.register(TissueType, TissueAdmin)
admin.site.register(BrainBlock)
admin.site.register(BrainRegion, TissueAdmin)
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
admin.site.register(OtherTissueSample, OtherTissueSampleAdmin)
admin.site.register(Publication)
