__author__ = 'farro'
from django.http import HttpResponseRedirect
from django.conf import settings
import re

class EnforceLoginMiddleware(object):
	"""
	http://djangosnippets.org/snippets/1158/

	Changes made from snippet:
		Hardcoded URL login.  This shouldn't ever change for matrr
		Defaults to allowing login page, regardless of PUBLIC_URLS existence.  Stops inf loops.
		Removed STATIC shenanigans.  I think it was required for older Django, but we don't seem to need it.
	"""

	def __init__(self):
		self.login_url = '/accounts/login/'
		public_urls = [(re.compile("^%s$" % ( self.login_url[1:] )))]
		if hasattr(settings,'PUBLIC_URLS'):
			public_urls += [re.compile(url) for url in settings.PUBLIC_URLS]
		self.public_urls = tuple(public_urls)

	def process_request(self, request):
		"""
		Redirect anonymous users to login_url from non public urls
		"""
		try:
			if request.user.is_anonymous() or not request.user.account.verified:
				for url in self.public_urls:
					if url.match(request.path[1:]):
						return None
				if  not request.user.account.verified:
					return HttpResponseRedirect('/not-verified')
				return HttpResponseRedirect("%s?next=%s" % (self.login_url, request.path))
			
		except AttributeError: #  I have no idea when this could happen.  *shrug*
			return HttpResponseRedirect("%s?next=%s" % (self.login_url, request.path))