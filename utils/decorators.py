from django.contrib import messages
from django.http import HttpResponseRedirect


"""
Format taken from:
	http://uswaretech.com/blog/2009/06/understanding-decorators/
"""
class supported_browser(object):
##  Unused. Now handled by matrr/context_processors.py
##  Still, this is a simple example of a useful tool
	def __init__(self, orig_func):
			self.orig_func = orig_func

	def __call__(self, request, *args, **kwargs):
		if 'MSIE' in request.META['HTTP_USER_AGENT']:
#			return HttpResponseRedirect('/browser/')
			messages.warning(request, "Unsupported Browser.  <link to info>")
			return self.orig_func(request, *args, **kwargs)
		else:
			return self.orig_func(request, *args, **kwargs)
