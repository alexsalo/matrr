from django.contrib import admin
from django.contrib.auth.models import User

from matrr.models import *
from matrr.forms import OtOAcountForm


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


class MonkeyAdmin(admin.ModelAdmin):
    readonly_fields = ('mky_age_at_intox',)
    list_display = ['mky_id', 'cohort', 'mky_real_id', 'mky_name', 'mky_species', 'mky_gender', 'mky_drinking']
    list_filter = ('cohort', 'mky_gender', 'mky_species', 'mky_drinking', )


class ShipmentAdmin(admin.ModelAdmin):
    readonly_fields = ('user', 'shp_shipment_date', 'req_request')
    list_display = ['shp_shipment_id', 'user', 'shp_shipment_date', 'shp_shipment_status', 'req_request_pk', 'req_request_cohort', 'req_request_user']
    list_filter = ('req_request__cohort', 'shp_shipment_status', 'req_request__user', )

    def req_request_cohort(self, obj):
        return obj.req_request.cohort.coh_cohort_name
    req_request_cohort.short_description = 'Cohort'

    def req_request_user(self, obj):
        return obj.req_request.user.username
    req_request_user.short_description = 'Requesting User'

    def req_request_pk(self, obj):
        return obj.req_request.pk
    req_request_pk.short_description = 'Request'



class RequestAdmin(admin.ModelAdmin):
    list_display = ['req_request_id', 'cohort', 'user', 'req_request_date', 'req_status']
    list_filter = ('cohort', 'req_status', 'req_request_date', 'user')


class TissueRequestAdmin(admin.ModelAdmin):
    list_display = ['get_req_request_pk', 'get_cohort', 'get_user', 'tissue_type', 'rtt_fix_type', 'rtt_prep_type', 'rtt_amount', 'rtt_units']
    list_filter = ('req_request__cohort', 'rtt_fix_type', 'rtt_prep_type', 'req_request__req_status', 'tissue_type', 'req_request__user')

    def get_req_request_pk(self, obj):
        return obj.req_request.pk
    get_req_request_pk.short_description = 'Request ID'

    def get_cohort(self, obj):
        return obj.req_request.cohort.coh_cohort_name
    get_cohort.short_description = 'Cohort'

    def get_user(self, obj):
        return obj.req_request.user.username
    get_user.short_description = 'Username'


class UserAdmin(admin.ModelAdmin):
    model = User
    list_display = ['username', 'email', 'first_name', 'last_name', 'date_joined']


class VerificationAccountAdmin(admin.ModelAdmin):
    list_display = ['username', 'first_name', 'last_name', 'email', 'institution', 'verified']
    list_filter = ['institution', 'act_state', 'act_country', 'verified']

    readonly_fields = ['username', 'first_name', 'last_name', 'act_real_address1', 'act_real_address1',
                       'act_real_address2', 'act_real_city', 'act_real_state', 'act_real_country', 'act_shipping_name',
                       'email', 'phone_number', 'institution', 'act_address1', 'act_address2', 'act_city', 'act_state',
                       'act_country', 'act_fedex']
    fieldsets = (
    ('Account information', {
    'fields': ('username', 'first_name', 'last_name', 'email', 'phone_number', 'institution', 'verified'),
    }),

    ('Address', {
    'fields': ('act_real_address1', 'act_real_address2', 'act_real_city', 'act_real_state', 'act_real_country'),
    }),

    ('Shipping information', {
    'fields': (
    'act_shipping_name', 'act_address1', 'act_address2', 'act_city', 'act_state', 'act_country', 'act_fedex'),
    'classes': ('collapse',),
    }),
    )

class DataSymposiumAdmin(admin.ModelAdmin):
    list_display = ['dsm_last_name', 'dsm_badge_name', 'dsm_role', 'dsm_hotel', 'dsm_reception', 'dsm_lunch', 'dsm_poster', 'dsm_diet']
    list_filter = ['dsm_role', 'dsm_reception', 'dsm_lunch', 'dsm_poster', 'dsm_diet']


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(TissueType, TissueAdmin)
admin.site.register(TissueCategory)
admin.site.register(Cohort)
admin.site.register(CohortEvent)
admin.site.register(CohortData)
admin.site.register(EventType)
admin.site.register(Monkey, MonkeyAdmin)
admin.site.register(Shipment, ShipmentAdmin)
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
admin.site.register(TissueRequest, TissueRequestAdmin)
admin.site.register(TissueRequestReview)
admin.site.register(Permission)
admin.site.register(DataSymposium, DataSymposiumAdmin)

