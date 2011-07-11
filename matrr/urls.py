__author__ = 'soltau'

from django.conf.urls.defaults import patterns, include, url
from django.conf import settings

from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from matrr.views import *


urlpatterns = patterns('django.views.generic.simple',
  url( r'^$',  MatrrTemplateView.as_view( template_name='matrr/index.html' )),
  url( r'^about/?$', TemplateView.as_view( template_name='matrr/about.html')),
  url( r'^benefits/?$', TemplateView.as_view( template_name='matrr/benefits.html')),
  url( r'^denied/?$', TemplateView.as_view( template_name='matrr/denied.html')),
  url( r'^events/$',
      ListView.as_view(
        queryset=Event.objects.filter(date__gte=datetime.now()).order_by('date', 'name'),
        context_object_name='event_list',
        template_name='matrr/events.html',
        paginate_by=10,
      )),
  url( r'^archived-events/$',
      ListView.as_view(
        queryset=Event.objects.filter(date__lt=datetime.now()).order_by('-date', 'name'),
        context_object_name='event_list',
        template_name='matrr/archived-events.html',
        paginate_by=10,
      )),
)

urlpatterns += patterns('matrr.views',
  url( r'^upcoming/$',
      ListView.as_view(
        queryset=Cohort.objects.filter(coh_upcoming=True).order_by('coh_cohort_name'),
        context_object_name='cohort_list',
        template_name='matrr/upcoming_cohorts.html',
        paginate_by=5
      ) ),
  url( r'^available/$',
      ListView.as_view(
        queryset=Cohort.objects.filter(coh_upcoming=False).order_by('coh_cohort_name'),
        context_object_name='cohort_list',
        template_name='matrr/available_cohorts.html',
        paginate_by=5,
      ) ),
  url( r'^cohort/$',
      ListView.as_view(
        queryset=Cohort.objects.order_by('coh_cohort_name'),
        context_object_name='cohort_list',
        template_name='matrr/upcoming_cohorts.html',
        paginate_by=5
      ) ),
  url( r'^cohort/(?P<pk>\d+)/$',
      DetailView.as_view(
        queryset=Cohort.objects.all(),
        context_object_name='cohort',
        template_name='matrr/cohort.html',
      ) ),
  url( r'^cohort/(?P<pk>\d+)/publications/$',
      DetailView.as_view(
        queryset=Cohort.objects.all(),
        context_object_name='cohort',
        template_name='matrr/publications.html',
      ) ),
  url( r'^upcoming/(?P<pk>\d+)/$',
      DetailView.as_view(
        queryset=Cohort.objects.filter(coh_upcoming=True),
        context_object_name='cohort',
        template_name='matrr/cohort.html',
      ) ),
  url( r'^available/(?P<pk>\d+)/$',
      DetailView.as_view(
        queryset=Cohort.objects.filter(coh_upcoming=False),
        context_object_name='cohort',
        template_name='matrr/cohort.html',
      )),
    url( r'^upcoming/(?P<pk>\d+)/timeline$',
      DetailView.as_view(
        queryset=Cohort.objects.filter(coh_upcoming=True),
        context_object_name='cohort',
        template_name='matrr/timeline.html',
      ) ),
  url( r'^available/(?P<pk>\d+)/timeline$',
      DetailView.as_view(
        queryset=Cohort.objects.filter(coh_upcoming=False),
        context_object_name='cohort',
        template_name='matrr/timeline.html',
      )),
  url( r'^(available|upcoming)/(?P<cohort_id>\d+)/monkey/(?P<monkey_id>\d+)/$',
      'monkey_cohort_detail_view'),
  url( r'^(available|upcoming)/(?P<pk>\d+)/tissues/$',
      DetailView.as_view( queryset=Cohort.objects.filter(),
                          context_object_name='cohort',
                          template_name='matrr/tissue_shopping_landing.html')),
  url( r'^(available|upcoming)/(?P<pk>\d+)/publications/$',
      DetailView.as_view( queryset=Cohort.objects.filter(),
                          context_object_name='cohort',
                          template_name='matrr/publications.html')),
  url( r'^publications/$',
      ListView.as_view(
        queryset=Publication.objects.all(),
        context_object_name='publications',
        template_name='matrr/all_publications.html',
        paginate_by=10,
      ) ),
  url( r'^(?P<static_page>privacy|data|usage)/$', static_page_view),
  url( r'^cart/$',
      cart_view),
  url( r'^cart/delete/?$',
      cart_delete),
  url( r'^cart/checkout/$',
      cart_checkout),
  url( r'^reviews/$',
      reviews_list_view),
  url( r'^reviews/(?P<review_id>\d+)/$',
      review_detail),
  url( r'^reviews_overviews/$',
      review_overview_list),
  url( r'^reviews_overviews/(?P<req_request_id>\d+)/$',
      review_overview),
  url( r'^reviews_overviews/(?P<req_request_id>\d+)/process/?$',
      request_review_process),
  url( r'^orders/$',
      orders_list),
  url( r'^orders/(?P<req_request_id>\d+)/$',
      order_detail),
  url( r'^orders/(?P<req_request_id>\d+)/delete/?$',
      order_delete),
  url( r'^experimental_plans/(?P<plan>\S+)/?$',
      experimental_plan_view),
  url( r'^account/$',
      account_view),
  url( r'^account/shipping/$',
      account_shipping),
  url( r'^mta/upload/$',
      mta_upload),
  url( r'^monkeys/(?P<monkey_id>\S+)/$',
      monkey_detail_view),
  url( r'^(available|upcoming)/(?P<cohort_id>\d+)/tissues/(?P<tissue_model>regions|samples|peripherals)/$',
      tissue_list),
  url( r'^(available|upcoming)/(?P<cohort_id>\d+)/tissues/(?P<tissue_model>regions|samples|peripherals)/(?P<tissue_id>\d+)/$',
      tissue_shop_detail_view),
  url( r'^(available|upcoming)/(?P<cohort_id>\d+)/tissues/custom/$',
      tissue_shop_custom_detail_view),
  url( r'^cart/(?P<tissue_model>regions|samples|peripherals|custom)/(?P<tissue_request_id>\d+)/$',
    cart_item_view),
  url( r'^cart/(?P<tissue_model>regions|samples|peripherals|custom)/(?P<tissue_request_id>\d+)/delete/$',
      cart_item_delete),
  url(r'^shipping_overview/$',
    shipping_overview),
  url(r'^account/(?P<user_id>\d+)/$',
    account_reviewer_view),
  url(r'^contact_us/$',
    contact_us),
  url(r'^shipping/build/(?P<req_request_id>\d+)/$',
    build_shipment),
  url(r'^shipping/build/(?P<req_request_id>\d+)/manifest/$',
    make_shipping_manifest_latex),
#  url(r'^search/?$',
#    search),
)

if settings.DEVELOPMENT:
  urlpatterns += patterns('matrr.views',
    url(r'^search/?$',
      search),
  )

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
