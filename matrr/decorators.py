from django.http import Http404
from django.shortcuts import redirect

def user_owner_test(test_func, arg_name, redirect_url=None):

	def decorator(view_func):

		def _wrapped_view(request, *args, **kwargs):
			param = kwargs[arg_name]
			try:
				correct = test_func(request.user, param)
			except:
				raise Http404('This page does not exist.')
			if correct:
				return view_func(request, *args, **kwargs)

			return redirect(redirect_url)
		return _wrapped_view
	return decorator