from django.conf.urls import patterns, include, url
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic import RedirectView
from django.contrib import admin
from views import cart, account, orders, review, rna, rud_reports, shipping, export
from views import uploads, verification, inventory, ajax, basic, tools, display, data, symposium
from settings import MEDIA_URL, MEDIA_ROOT, PRODUCTION
admin.autodiscover()

urlpatterns = patterns('',
    url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
    url(r'^admin/', include(admin.site.urls)),
    url(r'^accounts/register/$', basic.RegistrationView.as_view(), name='registration_register'), # this overrides the registration.backend.default.urls url endpoint.
    url(r'^accounts/', include('registration.backends.default.urls')),
    url(r'^favicon\.ico$', RedirectView.as_view(url='/static/images/favicon.ico')),
    url(r'^robots\.txt$', RedirectView.as_view(url='/static/robots.txt')),
    )

urlpatterns += staticfiles_urlpatterns()


urlpatterns += patterns('',
    ## Miscellaneous views.  Many of these are public facing
    url(r'^$', basic.index_view, name='matrr-home'),
    url(r'^logout/$', basic.logout, name='matrr-logout'),
    url(r'^(?P<static_page>privacy|data|usage|browser|faq|public-faq|about|benefits|denied|fee|safety|not-verified)/$', basic.pages_view), #  These are non-dynamic pages. Mostly text/html.
    url(r'^contact_us/$', basic.contact_us, name='contact-us'),
    url(r'^search/$', basic.search, name='search'),
    url(r'^advanced_search/$', basic.advanced_search, name='advanced-search'),
    url(r'^dynamic_cohorts_timeline/$', basic.dynamic_cohorts_timeline, name='dynamic-cohorts-timeline'),
    url(r'^publications/$', basic.publications, name='publications'),
    url(r'^mta/list/$', basic.mta_list, name='mta-list'), # not public facing, but it doesn't really belong anywhere else

    url(r'^events/$', display.event_list, name='events'),
    url(r'^archived-events/$', display.archived_event_list, name='archived-events'),
    url(r'^cohort/(?P<pk>\d+)/publications/$', display.cohort_publication_list, name='cohort-publications'),
)
urlpatterns += patterns('',
    ## Monkey/Cohort/Tissue display views
    url(r'^data_repository_grid/$', display.data_repository_grid, name='data-repository-grid'),
    url(r'^monkey_hormone_challenge_data_grid/$', display.monkey_hormone_challenge_data_grid, name='data-grid-monkey-hormone-challenge'),
    url(r'^available/$', display.cohorts_view_available, name='available'),
    url(r'^upcoming/$', display.cohorts_view_upcoming, name='upcoming'),
    url(r'^cohort/$', display.cohorts_view_all, name='cohorts'),
    url(r'^assay/$', display.cohorts_view_assay, name='assay'),

    url(r'^drinking_category_definition/$', display.drinking_category_definition, name='drinking-category-definition'),

    url(r'^cohort/(?P<pk>\d+)/$', display.cohort_details, name='cohort-details'),
    url(r'^cohort/(?P<coh_id>\d+)/upload/$', uploads.cod_upload, name='cod-upload'),
    url(r'^cohort/(?P<pk>\d+)/timeline$', display.cohort_timeline, name='cohort-timeline'),
    url(r'^cohort/(?P<coh_id>\d+)/monkey/(?P<mky_id>\d+)/$', display.monkey_cohort_detail_view, name='monkey-detail'),
    url(r'^monkey/(?P<mky_id>\d+)/$', display.monkey_detail_view, name='monkey-detail'),
    url(r'^cohort/(?P<coh_id>\d+)/tissues/$', display.tissue_shop_landing_view, name='tissue-shop-landing'),
    url(r'^cohort/(?P<coh_id>\d+)/tissues/(?P<tissue_category>[^/]*)/$', display.tissue_list, name='tissue-category'),
    url(r'^cohort/(?P<coh_id>\d+)/tissues/add-to-cart/(?P<tissue_id>\d+)/$', display.tissue_shop_detail_view, name='tissue-shop-detail'),
)

urlpatterns += patterns('',
    ##  Cart Views
    url(r'^cart/$', cart.cart_view, name='cart'),
    url(r'^cart/delete/?$', cart.cart_delete, name='cart-delete'),
    url(r'^cart/checkout/$', cart.cart_checkout, name='cart-checkout'),
    url(r'^cart/(?P<tissue_request_id>\d+)/$', cart.cart_item_view, name='cart-item'),
    url(r'^cart/(?P<tissue_request_id>\d+)/delete/$', cart.cart_item_delete, name='cart-item-delete'),
)

urlpatterns += patterns('',
    ##  Export Views
    url(r'^cohort/(?P<coh_id>\d+)/export/$', export.export_cohort_data, name='export-cohort-data'),
)

urlpatterns += patterns('',
    ##  Order processing views
    # order revision/submission/deletion
    url(r'^orders/$', orders.orders_list, name='order-list'),
    url(r'^orders/user/(?P<user_id>\d+)/$', orders.orders_list, name='order-list'),
    url(r'^orders/(?P<req_request_id>\d+)/$', orders.order_detail, name='order-detail'),
    url(r'^orders/(?P<req_request_id>\d+)/delete/$', orders.order_delete, name='order-delete'),
    url(r'^orders/(?P<req_request_id>\d+)/revise/$', orders.order_revise, name='order-revise'),
    url(r'^orders/(?P<req_request_id>\d+)/revise/confirm/$', orders.order_revise_confirm, name='order-revise-confirm'),
    url(r'^orders/(?P<req_request_id>\d+)/duplicate/$', orders.order_duplicate, name='order-duplicate'),
    url(r'^orders/(?P<req_request_id>\d+)/duplicate/confirm/$', orders.order_duplicate_confirm, name='order-duplicate-confirm'),
    url(r'^orders/(?P<req_request_id>\d+)/edit/$', orders.order_edit, name='order-edit'),
    url(r'^orders/(?P<req_request_id>\d+)/checkout/$', orders.order_checkout, name='order-checkout'),
    url(r'^orders/edit-tissue/(?P<req_rtt_id>\d+)/$', orders.order_edit_tissue, name='orders-edit-tissue'),
    url(r'^orders/delete-tissue/(?P<req_rtt_id>\d+)/$', orders.order_delete_tissue, name='orders-delete-tissue'),
    #  Order review
    url(r'^reviews/$', review.reviews_list_view, name='review-list'),
    url(r'^reviews/(?P<review_id>\d+)/$', review.review_detail, name='review-detail'),
    url(r'^reviews_overviews/$', review.review_overview_list, name='review-overview-list'),
    url(r'^reviews_history/$', review.review_history_list, name='review-history-list'),
    url(r'^reviews_overviews/(?P<req_request_id>\d+)/$', review.review_overview, name='review-overview'),
    url(r'^reviews_overviews/(?P<req_request_id>\d+)/price/$', review.review_overview_price, name='review-overview-price'),
    url(r'^reviews_overviews/(?P<req_request_id>\d+)/process/?$', review.request_review_process, name='review-overview-process'),
    # Shipping
    url(r'^shipping/overview/$', shipping.shipping_overview, name='shipping-overview'),
    url(r'^shipping/status/$', shipping.shipping_status, name='shipping-status'),
    url(r'^shipping/history/$', shipping.shipping_history, name='shipping-history'),
    url(r'^shipping/history/(?P<user_id>\d+)/$', shipping.shipping_history_user, name='shipping-history-user'),
    url(r'^shipping/creator/(?P<req_request_id>\d+)/$', shipping.shipment_creator, name='shipment-creator'),
    url(r'^shipping/processing/(?P<shipment_id>\d+)/$', shipping.shipment_processing, name='shipment-processing'),
    url(r'^shipping/detail/(?P<shipment_id>\d+)/$', shipping.shipment_detail, name='shipment-detail'),
    url(r'^shipping/detail/(?P<shipment_id>\d+)/manifest/$', shipping.shipment_manifest_export, name='shipment-manifest'),
)

urlpatterns += patterns('',
    ##  Account views
    url(r'^account/$', account.account_view, name='account-view'),
    url(r'^account/(?P<user_id>\d+)/$', account.account_reviewer_view, name='account-reviewer-view'),
    url(r'^account/shipping/$', account.account_shipping, name='account-shipping'),
    url(r'^account/address/$', account.account_address, name='account-address'),
    url(r'^account/info/$', account.account_info, name='account-info'),
    url(r'^account/mta/$', account.account_mta, name='account-mta'),
    url(r'^accunt/mta/upload/$', uploads.mta_upload, name='mta-upload'),
    url(r'^account/verify/(?P<user_id>\d+)/$', account.account_verify, name='account-verify'),
)

urlpatterns += patterns('',
    ## Research update views
    url(r'^rud/$', rud_reports.rud_update, name='rud-upload'),
    url(r'^rud/(?P<rud_id>\d+)', rud_reports.rud_detail, name='rud-detail'),
    url(r'^rud/list$', rud_reports.rud_list, name='rud-list'),
    url(r'^rud/overdue$', rud_reports.rud_overdue, name='rud-overdue'),
    url(r'^rud/in_progress$', rud_reports.rud_progress, name='rud-in-progress'),
    url(r'^rud/complete$', rud_reports.rud_progress, name='rud-complete'),
)

urlpatterns += patterns('',
    ## Inventory Verification views
    url(r'^verification/$', verification.tissue_verification, name='verification'),
    url(r'^verification/(?P<req_request_id>\d+)/$', verification.tissue_verification_list, name='verification-list'),
    url(r'^verification/(?P<req_request_id>\d+)/export$', verification.tissue_verification_export, name='verification-list-export'),
    url(r'^verification/inventory/(?P<cohort_pk>\d+)$', verification.tissue_verification_post_shipment, name='verification-inventory'),
    url(r'^verification/inventory/(?P<cohort_pk>\d+)/export$', verification.tissue_verification_export, name='verification-inventory-export'),
    url(r'^verification/(?P<req_request_id>\d+)/(?P<tiv_id>\d+)/$', verification.tissue_verification_detail, name='verification-detail'),
)

urlpatterns += patterns('',
    ## Inventory views
    url(r'^inventory/$', inventory.inventory_landing, name='inventory'),
    url(r'^inventory/cohort/(?P<coh_id>\d+)/$', inventory.inventory_cohort, name="inventory-cohort"),
    url(r'^inventory/cohort/(?P<coh_id>\d+)/brains/$', inventory.inventory_brain_cohort, name="inventory-brain-cohort"),
    url(r'^inventory/monkey/(?P<mig_id>\d+)/brains/$', inventory.inventory_brain_monkey, name="inventory-brain-monkey"),
    url(r'^inventory/data/$', inventory.DataIntegrationTrackingView.as_view(), name='data-integration-tracking'),
)

urlpatterns += patterns('',
    ## RNA views
    url(r'^rna/$', rna.rna_landing, name='rna-landing'),
    url(r'^rna/(?P<coh_id>\d+)/submit$', rna.rna_submit, name='rna-submit'),
    url(r'^rna/(?P<coh_id>\d+)/display$', rna.rna_display, name='rna-display'),
    url(r'^rna/detail/(?P<rna_id>\d+)$', rna.rna_detail, name='rna-detail'),
)

urlpatterns += patterns('',
    ## Tools views
    url(r'^tools/$', tools.tools_landing, name='tools-landing'),
    # Sandboxes
    url(r'^tools/sandbox/$', tools.tools_sandbox, name='tools-sandbox'),
    url(r'^tools/sandbox/genealogy/$', tools.tools_sandbox_familytree, name='tools-genealogy'),
    url(r'^tools/supersandbox/$', tools.tools_supersandbox, name='tools-supersandbox'),
    # Confederates
    url(r'^tools/confederates/$', tools.tools_confederates, name='tools-confederates'),
    url(r'^tools/confederates/chord$', tools.tools_confederates_chord_diagram, name='tools-confederates-chord'),
    url(r'^tools/confederates/adjacency$', tools.tools_confederates_adjacency_matrix, name='tools-confederates-adjacency'),
    # Proteins
    url(r'^tools/protein/$', tools.tools_protein, name='tools-protein'),
    url(r'^tools/protein/cohort/(?P<coh_id>\d+)/$', tools.tools_cohort_protein, name='tools-cohort-protein'),
    url(r'^tools/protein/cohort/(?P<coh_id>\d+)/graphs$', tools.tools_cohort_protein_graphs, name='tools-cohort-protein-graphs'),
    url(r'^tools/protein/cohort/(?P<coh_id>\d+)/monkey/$', tools.tools_monkey_protein_graphs, name='tools-monkey-protein'),
    url(r'^tools/protein/cohort/(?P<coh_id>\d+)/monkey/(?P<mky_id>\d+)/$', tools.tools_monkey_protein_graphs, name='tools-monkey-protein'),
    # Hormones
    url(r'^tools/hormone/$', tools.tools_hormone, name='tools-hormone'),
    url(r'^tools/hormone/cohort/(?P<coh_id>\d+)/$', tools.tools_cohort_hormone, name='tools-cohort-hormone'),
    url(r'^tools/hormone/cohort/(?P<coh_id>\d+)/graphs$', tools.tools_cohort_hormone_graphs, name='tools-cohort-hormone-graphs'),
    url(r'^tools/hormone/cohort/(?P<coh_id>\d+)/monkey/$', tools.tools_monkey_hormone_graphs, name='tools-monkey-hormone'),
    url(r'^tools/hormone/cohort/(?P<coh_id>\d+)/monkey/(?P<mky_id>\d+)/$', tools.tools_monkey_hormone_graphs, name='tools-monkey-hormone'),
    # ETOH
    url(r'^tools/etoh/cohort/(?P<cohort_method>[a-zA-Z_]+)/$', tools.tools_cohort_etoh_graphs, name='tools-cohort-etoh-graphs'),
    url(r'^tools/etoh/monkey/(?P<monkey_method>[a-zA-Z_]+)/$', tools.tools_monkey_etoh, name='tools-monkey-etoh'),
    url(r'^tools/etoh/monkey/(?P<monkey_method>[a-zA-Z_]+)/(?P<coh_id>\d+)/$', tools.tools_monkey_etoh_graphs, name='tools-monkey-etoh-graphs'),
    url(r'^tools/etoh/mtd-graph/(?P<mtd_id>\d+)$', tools.tools_etoh_mtd, name='tools-etoh-mtd'),
    # BEC
    url(r'^tools/bec/cohort/(?P<cohort_method>.+)/$', tools.tools_cohort_bec_graphs, name='tools-cohort-bec-graphs'),
    url(r'^tools/bec/monkey/(?P<monkey_method>[a-zA-Z_]+)/$', tools.tools_monkey_bec, name='tools-monkey-bec'),
    url(r'^tools/bec/monkey/(?P<monkey_method>[a-zA-Z_]+)/(?P<coh_id>\d+)/$', tools.tools_monkey_bec_graphs, name='tools-monkey-bec-graphs'),
    # genealogy
    url(r'^tools/genealogy/$', tools.tools_genealogy, name='tools-genealogy'),
    url(r'^tools/genealogy/(?P<coh_id>\d+)/$', tools.tools_cohort_genealogy, name='tools-cohort-genealogy'),
    # Exports
#    url(r'^tools/graph-as-pdf/$', tools.create_pdf_fragment, name='pdf-fragment'),
    url(r'^tools/graph-as-pdf/(?P<klass>[^/]*)/(?P<imageID>\d+)/$', tools.create_pdf_fragment_v2, name='pdf-fragment'),
    url(r'^tools/graph-as-svg/(?P<klass>[^/]*)/(?P<imageID>\d+)/$', tools.create_svg_fragment, name='svg-fragment'),
)
urlpatterns += patterns('',
    ## data views
    url(r'^data/upload/$', uploads.raw_data_upload, name='raw-upload'),
    url(r'^data/download/$', data.data_landing, name='data-landing'),
    url(r'^data/download/(?P<data_type>[a-zA-Z_]+)/$', data.data_cohort, name='data-cohort'),
    url(r'^data/download/(?P<data_type>[a-zA-Z_]+)/(?P<coh_id>\d+)/$', data.data_cohort_dates, name='data-cohort-submit'),
    url(r'^data/view/$', data.view_dto_data, name='view-dto-data'),
)

urlpatterns += patterns('',
    ## symposium views
    url(r'^symposium/landing/$', symposium.symposium_landing, name='symposium-landing'),
    url(r'^symposium/instructions/$', symposium.symposium_instructions, name='symposium-instructions'),
    url(r'^symposium/registration/$', symposium.symposium_registration_pg1, name='symposium-registration'),
    url(r'^symposium/registration/(?P<dsm_id>\d+)/$', symposium.symposium_registration_pg2, name='symposium-registration-pg2'),
    url(r'^symposium/roster/$', symposium.symposium_roster, name='symposium-roster'),
    url(r'^symposium/roster/(?P<dsm_id>\d+)/$', symposium.symposium_roster_detail, name='symposium-roster-detail'),
)

urlpatterns += patterns('',
    ## ajax views, should not be visible by themselves
    url(r'^ajax/advanced_search$', ajax.ajax_advanced_search, name='ajax-advanced-search'),
)

urlpatterns += patterns('',
    ## Deprecated urls
    ## These urls are exist for legacy.  The name= should all appear in urls above, and thus all links inside
    ## MATRR should direct to the newer urls listed above.

    url(r'^upload/$', uploads.raw_data_upload, ),#name='raw-upload'),
    url(r'^upload/mta/$', uploads.mta_upload, ),#name='mta-upload'),
    url(r'^upload/cohort_data/(?P<coh_id>\d+)/$', uploads.cod_upload, ),#name='cod-upload'),
    url(r'^tools/data/$', data.data_landing, ),#name='data-landing'),
    url(r'^tools/data/(?P<data_type>[a-zA-Z_]+)/$', data.data_cohort, ),#name='data-cohort'),
    url(r'^tools/data/(?P<data_type>[a-zA-Z_]+)/(?P<coh_id>\d+)/$', data.data_cohort_dates, ),#name='data-cohort-submit'),
)

if PRODUCTION:
    urlpatterns += patterns('', url(r'^media/(?P<pk>.*)$', basic.sendfile), )
else:
    from django.views.static import serve
    _media_url = MEDIA_URL
    if _media_url.startswith('/'):
        _media_url = _media_url[1:]
        urlpatterns += patterns('', (r'^%s(?P<path>.*)$' % _media_url, serve, {'document_root': MEDIA_ROOT}))
    del (_media_url, serve)
