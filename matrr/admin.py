from matrr.models import *
from django.contrib import admin

class TissueAdminForm(admin.ModelAdmin):
  formfield_overrides = {
    models.ManyToManyField: {'widget': admin.widgets.FilteredSelectMultiple("Monkeys", is_stacked=False)},
  }

admin.site.register(TissueType, TissueAdminForm)
admin.site.register(BrainBlock)
admin.site.register(BrainRegion, TissueAdminForm)
admin.site.register(BloodAndGenetic, TissueAdminForm)
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
