from django.contrib import admin
from django.contrib.admin import SimpleListFilter

from matrr.models import *
from matrr.forms import OtOAcountForm


class CohortExcludeListFilter(SimpleListFilter):
    # Human-readable title which will be displayed in the
    # right admin sidebar just above the filter options.
    title = 'EXCLUDE cohort'

    # Parameter for the filter that will be used in the URL query.
    parameter_name = 'exclude_cohort'

    def lookups(self, request, model_admin):
        """
        Returns a list of tuples. The first element in each
        tuple is the coded value for the option that will
        appear in the URL query. The second element is the
        human-readable name for the option that will appear
        in the right sidebar.
        return (
            ('80s', ('in the eighties',)),
            ('90s', ('in the nineties',)),
        )
        """
        cohorts = model_admin.model.objects.all().values_list('cohorts', 'cohorts__coh_cohort_name').distinct()
        cohorts = cohorts.exclude(cohorts=None).order_by('cohorts__coh_cohort_name')
        cohorts = list(cohorts)
        cohorts.append(('none', 'none'), )
        return cohorts

    def queryset(self, request, queryset):
        """
        Returns the filtered queryset based on the value
        provided in the query string and retrievable via
        `self.value()`.
        # Compare the requested value (either '80s' or '90s')
        # to decide how to filter the queryset.
        if self.value() == '80s':
            return queryset.filter(birthday__gte=date(1980, 1, 1),
                                    birthday__lte=date(1989, 12, 31))
        if self.value() == '90s':
            return queryset.filter(birthday__gte=date(1990, 1, 1),
                                    birthday__lte=date(1999, 12, 31))
        """
        if not self.value():
            return queryset
        if self.value() == "none":
            return queryset.exclude(cohorts=None)
        return queryset.exclude(cohorts=self.value())


class PublicationAdmin(admin.ModelAdmin):
    list_display = ['title', 'authors', 'journal', 'get_cohorts', 'published_year', 'pmid', 'pmcid', 'isbn', 'cites_matrr']
    list_filter = ['cohorts', CohortExcludeListFilter, 'published_year', 'cites_matrr', 'journal']

    def get_cohorts(self, obj):
        return ", ".join(obj.cohorts.order_by('coh_cohort_name').values_list('coh_cohort_name', flat=True))
    get_cohorts.short_description = 'Cohorts'

    def get_cohort(self, obj):
        return obj.req_request.cohort.coh_cohort_name
    get_cohort.short_description = 'Cohort'

    def get_user(self, obj):
        return obj.req_request.user.username
    get_user.short_description = 'Username'


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
        return obj.req_rfequest.user.username
    req_request_user.short_description = 'Requesting User'

    def req_request_pk(self, obj):
        return obj.req_request.pk
    req_request_pk.short_description = 'Request'


class RequestAdmin(admin.ModelAdmin):
    list_display = ['req_request_id', 'cohort', 'user', 'req_request_date', 'req_status']
    list_filter = ('cohort', 'req_status', 'req_request_date', 'user')

class ResearchUpdateAdmin(admin.ModelAdmin):
    list_display = ['rud_date', 'rud_progress', 'req_request']
    list_filter = ('req_request__req_request_id', 'req_request__user')

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


class CohortEventAdmin(admin.ModelAdmin):
    list_display = ['cohort', 'event', 'cev_date',]
    list_filter = ['cohort', 'event', ]


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
admin.site.register(TissueType, TissueAdmin)
admin.site.register(TissueCategory)
admin.site.register(Cohort)
admin.site.register(CohortEvent, CohortEventAdmin)
admin.site.register(CohortData)
admin.site.register(EventType)
admin.site.register(Monkey, MonkeyAdmin)
admin.site.register(Shipment, ShipmentAdmin)
admin.site.register(DrinkingExperiment)
admin.site.register(MonkeyToDrinkingExperiment)
admin.site.register(Institution)
admin.site.register(Event)
admin.site.register(TissueSample, TissueSampleAdmin)
admin.site.register(Publication, PublicationAdmin)
admin.site.register(Mta)
admin.site.register(Account, VerificationAccountAdmin)
admin.site.register(Request, RequestAdmin)
admin.site.register(ResearchUpdate, ResearchUpdateAdmin)
admin.site.register(TissueInventoryVerification)
admin.site.register(TissueRequest, TissueRequestAdmin)
admin.site.register(TissueRequestReview)
admin.site.register(Permission)
admin.site.register(DataSymposium, DataSymposiumAdmin)
admin.site.register(DataFile, )

