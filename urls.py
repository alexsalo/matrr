from django.conf.urls.defaults import patterns, include, url
from django.conf import settings
from django.contrib.staticfiles.urls import staticfiles_urlpatterns
from django.views.generic.simple import redirect_to

# Uncomment the next two lines to enable the admin:
from django.contrib import admin

admin.autodiscover()

from django.contrib.auth import views as authviews

urlpatterns = patterns('',
					   # Uncomment the admin/doc line below to enable admin documentation:
					   url(r'^admin/doc/', include('django.contrib.admindocs.urls')),
					   # Uncomment the next line to enable the admin:
					   url(r'^admin/', include(admin.site.urls)),
					   url(r'accounts/register/$', 'matrr.views.basic.registration'),
					   url(r'^accounts/', include('registration.urls')),
					   url(r'^favicon\.ico$', redirect_to, {'url': '/static/images/favicon.ico'}),
					   url(r'^robots\.txt$', redirect_to, {'url': '/static/robots.txt'}),
					   )

urlpatterns += patterns('',
						#	(r'^static/(?P<path>.*)$', 'django.views.static.serve',
						#		 {'document_root': settings.STATIC_ROOT}),
	(r'^login/?$', authviews.login, {'template_name': 'login.html'}),
						#	(r'^%s' % I18JS_URL, 'django.views.i18n.javascript_catalog')
)

urlpatterns += staticfiles_urlpatterns()

urlpatterns += patterns('',
						url(r'', include('matrr.urls')),
						)
#handler500 = 'matrr.views.matrr_handler500'
