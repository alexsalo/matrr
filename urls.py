from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns

# Uncomment the next two lines to enable the admin:
from django.contrib import admin
admin.autodiscover()

from django.views.generic import DetailView, ListView
from django.views.generic.base import TemplateView
from django.views.generic.edit import FormView

from django.contrib.auth import views as authviews
from matrr.models import *
from matrr.views import *

urlpatterns = patterns('',
  # Examples:
  # url(r'^django_test/', include('django_test.foo.urls')),
  
  # Uncomment the admin/doc line below to enable admin documentation:
  # url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
  # Uncomment the next line to enable the admin:
  url( r'^admin/', include(admin.site.urls)),
  url( r'^accounts/', include('registration.urls')),
)

urlpatterns += patterns('',
  (r'^static/(?P<path>.*)$', 'django.views.static.serve',
        {'document_root': settings.MEDIA_ROOT}),
  (r'^login/?$', authviews.login, {'template_name': 'login.html'}),
  (r'^logout/?$', authviews.logout, {'template_name': 'login.html', 'next_page':'/'}),
)

urlpatterns += staticfiles_urlpatterns()

urlpatterns += patterns('django.views.generic.simple',
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
        paginate_by=10,
      ) ),
  url( r'^available/$', 
      ListView.as_view(
        queryset=Cohort.objects.filter(coh_upcoming=False).order_by('coh_cohort_name'),
        context_object_name='cohort_list',
        template_name='matrr/available_cohorts.html',
        paginate_by=10,
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
  url( r'^upcoming/(?P<cohort_id>\d+)/monkey/(?P<monkey_id>\d+)/$', 
      'monkey_cohort_detail_view'),
  url( r'^available/(?P<cohort_id>\d+)/monkey/(?P<monkey_id>\d+)/$', 
      'monkey_cohort_detail_view'),
  url( r'^upcoming/(?P<cohort_id>\d+)/tissues/$',
      TemplateView.as_view( template_name='matrr/tissue_shopping_landing.html')),
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
  url( r'^reviews_overviews/(?P<req_request_id>\d+)/accept/?$',
      request_review_accept),
  url( r'^orders/$',
      orders_list),
  url( r'^orders/(?P<req_request_id>\d+)/$',
      order_detail),
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
  url( r'^upcoming/(?P<cohort_id>\d+)/tissues/(?P<tissue_model>blocks|regions|microdissected|samples|peripherals)/$',
      tissue_list),
  url( r'^upcoming/(?P<cohort_id>\d+)/tissues/(?P<tissue_model>blocks|regions|microdissected|samples|peripherals)/(?P<tissue_id>\d+)/$',
      tissue_shop_detail_view),
  url( r'^cart/(?P<tissue_model>blocks|regions|microdissected|samples|peripherals)/(?P<tissue_request_id>\d+)/$',
    cart_item_view),
  url( r'^cart/(?P<tissue_model>blocks|regions|microdissected|samples|peripherals)/(?P<tissue_request_id>\d+)/delete/$',
      cart_item_delete),
  url(r'^shipping_overview/$',
    shipping_overview),
  url(r'^search/?$',
    search),
)

if settings.DEBUG:
  from django.views.static import serve
  _media_url = settings.MEDIA_URL
  if _media_url.startswith('/'):
    _media_url = _media_url[1:]
    urlpatterns += patterns('',
        (r'^%s(?P<path>.*)$' % _media_url,
        serve,
        {'document_root': settings.MEDIA_ROOT}))
  del(_media_url, serve)