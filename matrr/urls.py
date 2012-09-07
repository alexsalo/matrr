from django.db.models.aggregates import Count
from django.conf.urls.defaults import patterns, url
from django.views.generic import DetailView, ListView
from matrr.views import *
import settings

cohort_timeline = DetailView.as_view(
			queryset=Cohort.objects.filter(),
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
			), name='events'),
	url(r'^archived-events/$',
		ListView.as_view(
			queryset=Event.objects.filter(date__lt=datetime.now()).order_by('-date', 'name'),
			context_object_name='event_list',
			template_name='matrr/archived-events.html',
			paginate_by=10,
			), name='archieved-events'),
	url(r'^cohort/(?P<pk>\d+)/publications/$',
		DetailView.as_view(
			queryset=Cohort.objects.all(),
			context_object_name='cohort',
			template_name='matrr/publications.html',
			), name='cohort-publications'),

	url(r'^publications/$',
		ListView.as_view(
			queryset=Publication.objects.all().annotate(non_date=Count('pub_date')).order_by('-non_date', '-pub_date'),
			context_object_name='publications',
			template_name='matrr/all_publications.html',
			paginate_by=15,
			), name='publications'),
)
# Real views
urlpatterns += patterns('matrr.views',
	#  Basic views
	url(r'^$', index_view),
	url(r'^logout/?$', logout, name='matrr-logout'),
	url(r'^(?P<static_page>privacy|data|usage|browser|faq|public-faq|about|benefits|denied|fee|safety|not-verified)/$', pages_view),  #  These are non-dynamic pages. Mostly text/html.
	url(r'^contact_us/$', contact_us),
	url(r'^search/?$', search, name='search'),
	url(r'^advanced_search/?$', advanced_search, name='advanced-search'),

	#  Monkey/Cohort/Tissue display views
	url(r'^available/$', 	cohorts_view_available, name='available'),
	url(r'^upcoming/$',     cohorts_view_upcoming, name='upcoming'),
	url(r'^cohort/$',     cohorts_view_all, name='cohorts'),
	url(r'^assay/$',     cohorts_view_assay, name='assay'),

	url(r'^cohort/(?P<pk>\d+)/$', 			cohort_details, name='cohort-details'),
	url(r'^cohort/(?P<pk>\d+)/timeline$', 	cohort_timeline, name='cohort-timeline'),
	url(r'^cohort/(?P<cohort_id>\d+)/monkey/(?P<monkey_id>\d+)/$', 	monkey_cohort_detail_view, name='monkey-detail'),
	url(r'^cohort/(?P<cohort_id>\d+)/tissues/(?P<tissue_category>[^/]*)/$', 	tissue_list, name='tissue-category'),
	url(r'^cohort/(?P<cohort_id>\d+)/tissues/$', 								tissue_shop_landing_view, name='tissue-shop-landing'),
	url(r'^cohort/(?P<cohort_id>\d+)/tissues/add-to-cart/(?P<tissue_id>\d+)/$',     tissue_shop_detail_view, name='tissue-shop-detail'),

	#  Cart Views
	url(r'^cart/$', 			                            cart_view, name='cart'),
	url(r'^cart/delete/?$', 	                            cart_delete, name='cart-delete'),
	url(r'^cart/checkout/$', 	                            cart_checkout, name='cart-checkout'),
	url(r'^cart/(?P<tissue_request_id>\d+)/$', 				cart_item_view, name='cart-item'),
	url(r'^cart/(?P<tissue_request_id>\d+)/delete/$', 		cart_item_delete, name='cart-item-delete'),

	#  Ordering process views
	url(r'^orders/$',                                           orders_list, name='order-list'),
	url(r'^orders/(?P<req_request_id>\d+)/$', 					order_detail, name='order-detail'),
	url(r'^orders/(?P<req_request_id>\d+)/delete/$', 			order_delete, name='order-delete'),
	url(r'^orders/(?P<req_request_id>\d+)/revise/$', 			order_revise, name='order-revise'),
	url(r'^orders/(?P<req_request_id>\d+)/duplicate/$', 		order_duplicate, name='order-duplicate'),
	url(r'^orders/(?P<req_request_id>\d+)/edit/$',	 			order_edit, name='order-edit'),
	url(r'^orders/(?P<req_request_id>\d+)/checkout/$',	 		order_checkout, name='order-checkout'),
	url(r'^orders/edit-tissue/(?P<req_rtt_id>\d+)/$', 			order_edit_tissue, name='orders-edit-tissue'),
	url(r'^orders/delete-tissue/(?P<req_rtt_id>\d+)/$', 		order_delete_tissue, name='orders-delete-tissue'),	

	url(r'^shipping/overview/$',								shipping_overview, name='shipping-overview'),
	url(r'^shipping/history/$',									shipping_history, name='shipping-history'),
	url(r'^shipping/history/(?P<user_id>\d+)/$',				shipping_history_user, name='shipping-history-user'),
	url(r'^shipping/creator/(?P<req_request_id>\d+)/$', 		shipment_creator, name='shipment-creator'),
	url(r'^shipping/detail/(?P<shipment_id>\d+)/$', 			shipment_detail, name='shipment-detail'),
	url(r'^shipping/detail/(?P<shipment_id>\d+)/manifest/$', 	shipment_manifest_export, name='shipment-manifest'),

	#  Order review views
	url(r'^reviews/$', 						reviews_list_view, name='review-list'),
	url(r'^reviews/(?P<review_id>\d+)/$', 	review_detail, name='review-detail'),
	url(r'^reviews_overviews/$', 			review_overview_list, name='review-overview-list'),
	url(r'^reviews_history/$',              review_history_list, name='review-history-list'),
	url(r'^reviews_overviews/(?P<req_request_id>\d+)/$', 			review_overview, name='review-overview'),
	url(r'^reviews_overviews/(?P<req_request_id>\d+)/price/$', 		review_overview_price, name='review-overview-price'),
	url(r'^reviews_overviews/(?P<req_request_id>\d+)/process/?$', 	request_review_process, name='review-overview-process'),

	#  Account stuff
	url(r'^account/$', 					account_view, name='account-view'),
	url(r'^account/shipping/$', 		account_shipping, name='account-shipping'),
	url(r'^account/address/$',			account_address, name='account-address'),
	url(r'^account/info/$',				account_info, name='account-info'),
	url(r'^account/mta/$',         		account_mta, name='account-mta'),
	url(r'^account/verify/(?P<user_id>\d+)/$', account_verify, name='account-verify'),
	url(r'^account/(?P<user_id>\d+)/$', account_reviewer_view, name='account-reviewer-view'),

	#  MTA pages -.-
	url(r'^mta/list/$', 					mta_list, name='mta-list'),

	# Upload pages
	url(r'^upload/$', raw_data_upload, name='raw-upload'),
	url(r'^upload/mta/$', 				mta_upload, name='mta-upload'),
	url(r'^upload/research_update/$',   rud_upload, name='rud-upload'),
	url(r'^upload/cohort_data/(?P<coh_id>\d+)/$',   		cod_upload, name='cod-upload'),

	# Research update pages
	url(r'^rud/list$', research_update_list, name='rud-list'),
	url(r'^rud/overdue$', research_update_overdue, name='rud-overdue'),

	# Inventory Verification pages
	url(r'^verification/$', tissue_verification, name='verification'),
	url(r'^verification/(?P<req_request_id>\d+)/$', tissue_verification_list, name='verification-list'),
	url(r'^verification/(?P<req_request_id>\d+)/export$', tissue_verification_export, name='verification-list-export'),
	url(r'^verification/(?P<req_request_id>\d+)/(?P<tiv_id>\d+)/$', tissue_verification_detail, name='verification-detail'),

	url(r'^inventory/cohort/(?P<coh_id>\d+)/$', inventory_cohort, name="inventory-cohort"),
	url(r'^inventory/$', user_passes_test(lambda u: u.has_perm('matrr.browse_inventory'), login_url='/denied/')(ListView.as_view(
							model=Cohort,template_name="matrr/inventory/inventory.html")), name='inventory'),
	
	# Tools
	url(r'^tools/$', tools_landing, name='tools-landing'),
	url(r'^tools/sandbox/$', tools_sandbox, name='tools-sandbox'),

	url(r'^tools/protein/$', tools_protein, name='tools-protein'),
	url(r'^tools/protein/cohort/(?P<cohort_id>\d+)/$', tools_cohort_protein, name='tools-cohort-protein'),
	url(r'^tools/protein/cohort/(?P<cohort_id>\d+)/graphs$', tools_cohort_protein_graphs, name='tools-cohort-protein-graphs'),
	url(r'^tools/protein/cohort/(?P<cohort_id>\d+)/monkey/$', tools_monkey_protein_graphs, name='tools-monkey-protein'),
	url(r'^tools/protein/cohort/(?P<cohort_id>\d+)/monkey/(?P<monkey_id>\d+)/$', tools_monkey_protein_graphs, name='tools-monkey-protein'),

	url(r'^tools/etoh/$', tools_etoh, name='tools-etoh'),
	url(r'^tools/etoh/cohort/(?P<cohort_id>\d+)/$', tools_cohort_etoh, name='tools-cohort-etoh'),
	url(r'^tools/etoh/cohort/(?P<cohort_id>\d+)/graphs$', tools_cohort_etoh_graphs, name='tools-cohort-etoh-graphs'),
	url(r'^tools/etoh/cohort/(?P<cohort_id>\d+)/monkey/$', tools_monkey_etoh_graphs, name='tools-monkey-etoh'),
	url(r'^tools/etoh/cohort/(?P<cohort_id>\d+)/monkey/(?P<monkey_id>\d+)/$', tools_monkey_etoh_graphs, name='tools-monkey-etoh'),
	url(r'^tool/etoh/mtd-graph/(?P<mtd_id>\d+)$', tools_etoh_mtd, name='tools-etoh-mtd'),
	url(r'^tools/graph-as-pdf/$', create_pdf_fragment, name='pdf-fragment'),
	url(r'^tools/graph-as-svg/(?P<klass>[^/]*)/(?P<imageID>\d+)/$', create_svg_fragment, name='svg-fragment'),

	url(r'^tools/genealogy/$', tools_genealogy, name='tools-genealogy'),
	url(r'^tools/genealogy/(?P<cohort_id>\d+)/$', tools_cohort_genealogy, name='tools-cohort-genealogy'),

#	url(r'^tools/vip/graphs/mtd/(?P<mtd_id>[^/]*)$', vip_mtd_graph, name='vip-mtd-graph'),
	url(r'^tools/vip/graph_builder/(?P<method_name>[^/]*)$', vip_graph_builder, name='vip-graph-builder'),


	)

if settings.DEVELOPMENT:
#if False:
	from django.views.static import serve

	_media_url = settings.MEDIA_URL
	if _media_url.startswith('/'):
		_media_url = _media_url[1:]
		urlpatterns += patterns('',
			(r'^%s(?P<path>.*)$' % _media_url,
			 serve,
				 {'document_root': settings.MEDIA_ROOT}))
	del(_media_url, serve)
else:
	urlpatterns += patterns('matrr.views', url(r'^media/(?P<id>.*)$', sendfile),)
