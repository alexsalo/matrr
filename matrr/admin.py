from matrr.models import *
from django.contrib import admin

class TissueAdmin(admin.ModelAdmin):
  formfield_overrides = {
    models.ManyToManyField: {'widget': admin.widgets.FilteredSelectMultiple("Monkeys", is_stacked=False)},
  }
  list_filter = ('category', )
  search_fields = ['tst_tissue_name']

class TissueSampleAdmin(admin.ModelAdmin):
  actions = ['remove_samples_from_inventory',
             'update_inventory_dates']
  readonly_fields = ('tss_modified',)
  list_filter = ('monkey__cohort',
                 'monkey',
                 'tissue_type__category',
                 'tissue_type',
                 'tss_freezer', )

  def queryset(self, request):
    return TissueSample.objects

  def update_inventory_dates(self, request, queryset):
    for model in queryset.all():
      model.save()


admin.site.register(TissueType, TissueAdmin)
admin.site.register(TissueCategory)
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
admin.site.register(TissueSample, TissueSampleAdmin)
admin.site.register(Publication)
