#encoding=utf-8
from subprocess import call, PIPE
from os import remove
from os.path import dirname
from tempfile import NamedTemporaryFile
from django.template import loader, Context
from settings import PRODUCTION

'''
This is a snippet from http://djangosnippets.org/snippets/102/
'''

def process_latex(template, context={}, type='pdf', outfile=None):
	"""
		Processes a template as a LaTeX source file.
		Output is either being returned or stored in outfile (using outfile.write()).
		At the moment only pdf output is supported.
	"""

	t = loader.get_template(template)
	c = Context(context)
	r = t.render(c)

	tex = NamedTemporaryFile()
	tex.write(r)
	tex.flush()
	base = tex.name
	items = "log aux pdf dvi png".split()
	names = dict((x, '%s.%s' % (base, x)) for x in items)
	output = names[type]

	if type == 'pdf' or type == 'dvi':
		pdflatex(base, type)
	elif type == 'png':
		pdflatex(base, 'dvi')
		call(['dvipng', '-bg', '-transparent',
			  names['dvi'], '-o', names['png']],
											   cwd=dirname(base), stdout=PIPE, stderr=PIPE)

#	remove(names['log'])
#	remove(names['aux'])

	o = file(output).read()
	remove(output)
	if not outfile:
		return o
	else:
		outfile.write(o)
		#rename(output, outfile)
		return outfile


def pdflatex(file, type='pdf'):
	import os
	path = os.path.dirname(os.path.realpath(__file__))
	if PRODUCTION:
		call(['pdflatex', 	'-interaction=nonstopmode',
							'-output-format', type,
							'-fmt', path + "/pdflatex",
							file],
			  cwd=dirname(file), stdout=PIPE, stderr=PIPE)
	else:
		call(['pdflatex', 	'-interaction=nonstopmode',
							'-output-format', type,
							#'-fmt', "/web/www/pdflatex/pdflatex",
							file],
#			  cwd=dirname(file), stdout=PIPE, stderr=PIPE)
			  cwd=dirname(file))