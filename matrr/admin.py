from matrr.models import *
from django.contrib import admin
from django.contrib.auth.models import User
from matrr.forms import OtOAcountForm
from django.forms import CharField

class TissueAdmin(admin.ModelAdmin):
	formfield_overrides = {
		models.ManyToManyField: {'widget': admin.widgets.FilteredSelectMultiple("Monkeys", is_stacked=False)},
		}
	list_filter = ('category', )
	search_fields = ['tst_tissue_name']


class TissueSampleAdmin(admin.ModelAdmin):
	actions = ['remove_samples_from_inventory',
			   'update_inventory_dates']
	readonly_fields = ('tss_modified', "user")
	list_filter = ('monkey__cohort',
				   'monkey',
				   'tissue_type__category',
				   'tissue_type',
				   'tss_freezer',
					'user',)

	def queryset(self, request):
		return TissueSample.objects

	def update_inventory_dates(self, request, queryset):
		for model in queryset.all():
			model.save()


class RequestAdmin(admin.ModelAdmin):
	readonly_fields = ('req_report_asked',)


class UserAdmin(admin.StackedInline):
	model = User
	fk_name = 'account'
	fields = ['username','first_name', 'last_name', 'email']
	readonly_fields = ['username','first_name', 'last_name', 'email']

class VerificationAccountAdmin(admin.ModelAdmin):
	
	form = OtOAcountForm
	
	readonly_fields = ['username','verified', 'first_name', 'last_name','act_real_address1','act_real_address1', 'act_real_address2', 'act_real_city', 'act_real_state', 'act_real_country', 'act_shipping_name','email', 'phone_number', 'institution','act_address1', 'act_address2', 'act_city', 'act_state', 'act_country', 'act_fedex']
	fieldsets = (
				('Account information',{
									'fields':('username','first_name', 'last_name', 'email', 'phone_number', 'institution', 'verified'),
									}),
				('Address',{
							'fields':('act_real_address1', 'act_real_address2', 'act_real_city', 'act_real_state', 'act_real_country'),
						}),
				('Shipping information', {
										'fields': ('act_shipping_name','act_address1', 'act_address2', 'act_city', 'act_state', 'act_country', 'act_fedex'), 
										'classes': ('collapse',),
										}),
				)

admin.site.register(TissueType, TissueAdmin)
admin.site.register(TissueCategory)
admin.site.register(Cohort)
admin.site.register(CohortEvent)
admin.site.register(CohortData)
admin.site.register(EventType)
admin.site.register(Monkey)
admin.site.register(Shipment)
admin.site.register(DrinkingExperiment)
admin.site.register(MonkeyToDrinkingExperiment)
admin.site.register(Institution)
admin.site.register(Event)
admin.site.register(TissueSample, TissueSampleAdmin)
admin.site.register(Publication)
admin.site.register(Mta)
admin.site.register(Account, VerificationAccountAdmin)
admin.site.register(Request, RequestAdmin)
admin.site.register(TissueInventoryVerification)
admin.site.register(TissueRequest)
admin.site.register(TissueRequestReview)
admin.site.register(Permission)

