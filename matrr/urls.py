__author__ = 'soltau'

from django.conf.urls.defaults import patterns, url
from django.views.generic import DetailView, ListView
from matrr.views import *
import settings

cohort_timeline = DetailView.as_view(
            queryset=Cohort.objects.filter(),
            context_object_name='cohort',
            template_name='matrr/timeline.html',
            )


available_timeline = DetailView.as_view(
            queryset=Cohort.objects.filter(coh_upcoming=False),
            context_object_name='cohort',
            template_name='matrr/timeline.html',
            )
upcoming_timeline = DetailView.as_view(
            queryset=Cohort.objects.filter(coh_upcoming=True),
            context_object_name='cohort',
            template_name='matrr/timeline.html',
            )

# Pretend views
urlpatterns = patterns('matrr.views',
    url(r'^events/$',
        ListView.as_view(
            queryset=Event.objects.filter(date__gte=datetime.now()).order_by('date', 'name'),
            context_object_name='event_list',
            template_name='matrr/events.html',
            paginate_by=10,
            )),
    url(r'^archived-events/$',
        ListView.as_view(
            queryset=Event.objects.filter(date__lt=datetime.now()).order_by('-date', 'name'),
            context_object_name='event_list',
            template_name='matrr/archived-events.html',
            paginate_by=10,
            )),
	url(r'^(available|upcoming|cohort)/(?P<pk>\d+)/publications/$',
        DetailView.as_view(
            queryset=Cohort.objects.all(),
            context_object_name='cohort',
            template_name='matrr/publications.html',
            )),
    url(r'^upcoming/(?P<pk>\d+)/timeline$', upcoming_timeline, name='upcoming-timeline'),
    url(r'^cohort/(?P<pk>\d+)/timeline$', cohort_timeline, name='cohort-timeline'),
    url(r'^available/(?P<pk>\d+)/timeline$', available_timeline, name='available-timeline'),
    
    url(r'^(available|upcoming|cohort)/(?P<pk>\d+)/publications/$',
        DetailView.as_view(queryset=Cohort.objects.filter(),
			context_object_name='cohort',
			template_name='matrr/publications.html')),
    url(r'^publications/$',
        ListView.as_view(
            queryset=Publication.objects.all(),
            context_object_name='publications',
            template_name='matrr/all_publications.html',
            paginate_by=15,
            )),
)
# Real views
urlpatterns += patterns('matrr.views',
	#  Basic views
	url(r'^$', index_view),
	url(r'^(?P<static_page>privacy|data|usage|browser|faq|about|benefits|denied|fee|safety)/$', pages_view),  #  These are non-dynamic pages. Mostly text/html.
    url(r'^contact_us/$', contact_us),
	url(r'^search/?$', search),

	#  Monkey/Cohort/Tissue display views
	url(r'^monkeys/(?P<monkey_id>\S+)/$', 								monkey_detail_view),
	url(r'(?P<avail_up>^available|upcoming|cohort|assay)/$', 					display_cohorts),
	url(r'(?P<avail_up>^available|upcoming|cohort|assay)/(?P<pk>\d+)/$', 		display_cohorts),
#*** This is a hack, does nothing but display a message saying we don't have necropsy data.  This will need to be changed if/when we get a batch of necropsy data
    url(r'^(available|upcoming|cohort)/(?P<pk>\d+)/necropsy/$', 		cohort_necropsy, name="cohortnect"),
#***
#	url(r'^cohort/(?P<cohort_id>\d+)/monkey/(?P<monkey_id>\d+)/$', 		monkey_cohort_detail_view, name='monkey_detail_coh'),
#    url(r'^available/(?P<cohort_id>\d+)/monkey/(?P<monkey_id>\d+)/$', 	monkey_cohort_detail_view, name='monkey_detail_av'),
    url(r'^(?P<avail_up>^available|upcoming|cohort)/(?P<cohort_id>\d+)/monkey/(?P<monkey_id>\d+)/$', 	monkey_cohort_detail_view, name='monkey_detail'),
	url(r'^(?P<avail_up>^available|upcoming|cohort)/(?P<cohort_id>\d+)/tissues/(?P<tissue_category>[^/]*)/$', 	tissue_list),
	url(r'^(?P<avail_up>^available|upcoming|cohort)/(?P<cohort_id>\d+)/tissues/$', 								tissue_shop_landing_view, name='tissue-shop-landing'),
    url(r'^(?P<avail_up>^available|upcoming|cohort)/(?P<cohort_id>\d+)/tissues/[^/]*/?(?P<tissue_id>\d+)/$', 	tissue_shop_detail_view),

	#  Cart Views
	url(r'^cart/$', 			                            cart_view, name='cart'),
	url(r'^cart/delete/?$', 	                            cart_delete, name='cart-delete'),
	url(r'^cart/checkout/$', 	                            cart_checkout, name='cart-checkout'),
	url(r'^cart/(?P<tissue_request_id>\d+)/$', 				cart_item_view, name='cart-item'),
	url(r'^cart/(?P<tissue_request_id>\d+)/delete/$', 		cart_item_delete, name='cart-item-delete'),

	#  Ordering process views
    url(r'^orders/$',                                           orders_list, name='order-list'),
    url(r'^orders/(?P<req_request_id>\d+)/$', 					order_detail, name='order-detail'),
	url(r'^orders/(?P<req_request_id>\d+)/delete/?$', 			order_delete),
	url(r'^experimental_plans/(?P<plan>\S+)/?$', 				experimental_plan_view),
	url(r'^shipping_overview/$',								shipping_overview),
	url(r'^shipping/build/(?P<req_request_id>\d+)/$', 			build_shipment, name='build-shippment'),
	url(r'^shipping/build/(?P<req_request_id>\d+)/manifest/$', 	make_shipping_manifest_latex, name='manifest'),

	#  Order review views
	url(r'^reviews/$', 						reviews_list_view, name='review-list'),
	url(r'^reviews/(?P<review_id>\d+)/$', 	review_detail, name='review-detail'),
	url(r'^reviews_overviews/$', 			review_overview_list, name='review-overview-list'),
    url(r'^reviews_history/$',              review_history_list, name='review-history-list'),
	url(r'^reviews_overviews/(?P<req_request_id>\d+)/$', 			review_overview, name='review-overview'),
	url(r'^reviews_overviews/(?P<req_request_id>\d+)/process/?$', 	request_review_process, name='review-overview-process'),

	#  Account stuff
	url(r'^account/$', 					account_view, name='account-view'),
    url(r'^account/shipping/$', 		account_shipping, name='account-shipping'),
	url(r'^account/(?P<user_id>\d+)/$', account_reviewer_view, name='account-reviewer-view'),
	url(r'^mta/upload/$', 				mta_upload, name='mta-upload'),


	url(r'^verification/?$',
		tissue_verification),
	)

if settings.DEVELOPMENT:
    urlpatterns += patterns('matrr.views',
	)

# I don't know what this does.  if you understand it, please tell me.
# -jf
if settings.DEVELOPMENT:
    from django.views.static import serve

    _media_url = settings.MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]
        urlpatterns += patterns('',
            (r'^%s(?P<path>.*)$' % _media_url,
             serve,
                 {'document_root': settings.MEDIA_ROOT}))
    del(_media_url, serve)
