from itertools import chain
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import  force_unicode
from matrr.models import Availability, Monkey
from django.forms.util import flatatt
from django.core.urlresolvers import reverse
from django.forms import *
from django.forms.widgets import Input, RadioFieldRenderer
import re

def date_to_padded_int(date):
	return str(date.year) + str(date.month).zfill(2) + str(date.day).zfill(2)

#this class is supposed to be abstract
class CheckboxSelectMultipleLink(CheckboxSelectMultiple):
	def __init__(self, link_base, tissue, attrs=None, choices=()):
		self.tissue = tissue
		self.link_base = link_base
		super(CheckboxSelectMultipleLink, self).__init__(attrs, choices)

	def render(self, name, value, attrs=None, choices=()):
		if value is None: value = []
		has_id = attrs and 'id' in attrs
		final_attrs = self.build_attrs(attrs, name=name)
		output = [u'<fieldset><legend><input type=\'checkbox\' id=\'%s\' onclick=\'toggle_checked(this, "%s")\'> <label for=\'%s\'>Select All Monkeys</label></legend>' % (
		attrs['id'], name, attrs['id'])]
		output.append(u'<table class="full-width" ><thead><td></td><td>Monkey</td><td>Status</td><td>Assignment</td></thead>')
		# Normalize to strings
		str_values = set([force_unicode(v) for v in value])
		for i, (mky_id, mky_real_id) in enumerate(chain(self.choices, choices)):
			# If an ID attribute was given, add a numeric index as a suffix,
			# so that the checkboxes don't all have the same ID attribute.
			if has_id:
				final_attrs = dict(final_attrs,
								   id='%s_%s' % (attrs['id'], i),
								   onclick="check_toggler(document.getElementById('%s'), '%s')" %\
										   (attrs['id'], name))
				label_for = u' for="%s"' % final_attrs['id']
			else:
				label_for = ''

			cb = CheckboxInput(final_attrs,
							   check_test=lambda value: value in str_values, )
			mky_id = force_unicode(mky_id)
			rendered_cb = cb.render(name, mky_id)
			mky_real_id = conditional_escape(force_unicode(mky_real_id))

			monkey = Monkey.objects.get(mky_id=mky_id)

			if monkey.mky_drinking:
				assignment = 'Ethanol'
			elif monkey.mky_housing_control:
				assignment = 'Housing Control'
			else:
				assignment = 'Control'

			positive, status_str, color,  = self.get_status(monkey)
			if self.tissue:
				if not positive:
					output.append(
						u'<tr><td></td><td><a href=\'%s\' target=\'_blank\'>%s<img src="/static/images/arrow_popup.png" width="8" height="8" style=\'vertical-align: text-top\' alt="external link"/></a> </td><td><font color=%s>%s </font></td><td>%s</td></tr>' % (
						reverse('monkey-detail', args=[self.link_base, mky_id]),
						mky_real_id,
						color,
						status_str,
						assignment,))
				else:
					output.append(
						u'<tr><td><label%s>%s </label></td><td><a href=\'%s\' target=\'_blank\'>%s<img src="/static/images/arrow_popup.png" width="8" height="8" style=\'vertical-align: text-top\' alt="external link"/></a> </td><td><font color=green>%s </font></td><td>%s</td></tr>' % (
						label_for,
						rendered_cb,
						reverse('monkey-detail', args=[self.link_base, mky_id]),
						mky_real_id,
						status_str,
						assignment))
			else:
				# this is for custom tissue requests
				output.append(
					u'<tr><td><label%s>%s</label></td><td>%s<a href=\'%s\' target=\'_blank\'><img src="/static/images/arrow_popup.png" width="8" height="8" style=\'vertical-align: text-top\' alt="external link"/></a></td><td></td><td>%s</td></tr>' % (
					label_for,
					rendered_cb,
					reverse('monkey-detail', args=[self.link_base, mky_id]),
					mky_real_id,
					assignment))

		output.append(u'</table></fieldset>')
		output.append(u"<script type='text/javascript'>check_toggler(document.getElementById('%s'), '%s');</script>" %\
					  (attrs['id'], name))
		return mark_safe(u'\n'.join(output))


class CheckboxSelectMultipleLinkByTableNoVerification(CheckboxSelectMultipleLink):
	def get_status(self, monkey):
		availability = self.tissue.get_monkey_availability(monkey)
		if availability == Availability.Available:
			availability_str = 'Available'
			color = ""
			positive = True
		elif availability == Availability.In_Stock:
			availability_str = 'In Stock'
			positive = True
			color = ""
		elif availability == Availability.Unavailable:
			availability_str = 'Unavailable'
			positive = False
			color = "red"
		return positive, availability_str, color


class CheckboxSelectMultipleLinkByTable(CheckboxSelectMultipleLink):
	def __init__(self, link_base, tissue, tis_request, attrs=None, choices=()):
		self.tis_request = tis_request

		super(CheckboxSelectMultipleLinkByTable, self).__init__(link_base, tissue, attrs, choices)

	def get_status(self, monkey):
		verification, is_new = self.tissue.tissue_verification_set.get_or_create(monkey=monkey, tissue_request=self.tis_request)
		if verification.tiv_inventory == 'Unverified':
			color = "orange"
			positive = False
		elif verification.tiv_inventory == 'Insufficient':
			color = "red"
			positive = False
		else:
			color = ""
			positive = True
		return positive, verification.tiv_inventory, color


class FixTypeSelection(Input):
	'''
	  This widget will require some custom javascript in order for it to work.
	  '''

	def __init__(self, choices=(), attrs=None):
		self.choices = choices
		super(FixTypeSelection, self).__init__(attrs)

	def render(self, name, value, attrs=None, choices=()):
		if value is None: value = ''
		final_attrs = self.build_attrs(attrs, name=name)
		output = [u'<select id=\'%s_selection\' onchange=\'updateSelection("%s")\'>' % (final_attrs.get('id'), final_attrs.get('id'))]
		options = self.render_options(choices, [value])
		if options:
			output.append(options)
		output.append(u'</select>')
		if value != '':
			# Only add the 'value' attribute if a value is non-empty.
			final_attrs['value'] = force_unicode(self._format_value(value))
		output.append(u'<input class=\'hidden\' %s />' % flatatt(final_attrs))
		return mark_safe(u'\n'.join(output))

	def render_option(self, selected_choices, option_value, option_label):
		option_value = force_unicode(option_value)
		selected_html = (option_value in selected_choices) and u' selected="selected"' or ''
		return u'<option value="%s"%s>%s</option>' % (
		escape(option_value), selected_html,
		conditional_escape(force_unicode(option_label)))

	def render_options(self, choices, selected_choices):
		# Normalize to strings.
		selected_choices = set([force_unicode(v) for v in selected_choices])
		output = []
		for option_value, option_label in chain(self.choices, choices):
			if isinstance(option_label, (list, tuple)):
				output.append(u'<optgroup label="%s">' % escape(force_unicode(option_value)))
				for option in option_label:
					output.append(self.render_option(selected_choices, *option))
				output.append(u'</optgroup>')
			else:
				output.append(self.render_option(selected_choices, option_value, option_label))
		return u'\n'.join(output)

	def render_textbox(self, name, value, attrs=None, choices=()):
		if value is None:
			value = ''
		output = []
		# build a select field to choose between the provided choices
		#TODO

		# build the final text field
		final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
		if value != '':
			# Only add the 'value' attribute if a value is non-empty.
			final_attrs['value'] = force_unicode(self._format_value(value))
		output.append(u'<input class=\'hidden\' %s />' % flatatt(final_attrs))
		return mark_safe(u'\n'.join(output))


class GroupedCheckboxSelectMultipleMonkeys(CheckboxSelectMultiple):
	def __init__(self, tissue_request, attrs=None, choices=()):
		self.tissue_request = tissue_request
		super(GroupedCheckboxSelectMultipleMonkeys, self).__init__(attrs, choices)

	def render(self, name, value, attrs=None, choices=()):
		if value is None: value = []
		has_id = attrs and 'id' in attrs
		final_attrs = self.build_attrs(attrs, name=name)
		output = [u'<fieldset><legend><input type=\'checkbox\' id=\'%s\' onclick=\'toggle_checked(this, "%s")\'> <label for=\'%s\'>Select All Monkeys</label></legend>' % (
		attrs['id'], name, attrs['id'])]
		# Normalize to strings
		str_values = set([force_unicode(v) for v in value])
		for i, (mky_id, mky_real_id) in enumerate(chain(self.choices, choices)):
			# If an ID attribute was given, add a numeric index as a suffix,
			# so that the checkboxes don't all have the same ID attribute.
			if has_id:
				final_attrs = dict(final_attrs,
								   id='%s_%s' % (attrs['id'], i),
								   onclick="check_toggler(document.getElementById('%s'), '%s')" %\
										   (attrs['id'], name))
				label_for = u' for="%s"' % final_attrs['id']
			else:
				label_for = ''

			cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
			mky_id = force_unicode(mky_id)
			rendered_cb = cb.render(name, mky_id)
			rendered_cb = re.sub('&#39;', '\'', rendered_cb)
			mky_real_id = conditional_escape(force_unicode(mky_real_id))
			link = '/monkeys/' + str(mky_real_id)
			output.append(
				u'<label%s>%s <a href=\'%s\' target=\'_blank\'><img src="/static/images/arrow_popup.png" width="8" height="8" style=\'vertical-align: text-top\' alt="external link"/>%s</a></label>' %\
				(label_for,
				 rendered_cb,
				 #				 link,
				 link,
				 mky_real_id))
		output.append(u'</fieldset>')
		return mark_safe(u'\n'.join(output))


# -*- coding: utf-8 -*-   // i dunno if this is important -jf
'''
http://djangosnippets.org/snippets/1629/

DateTimeWidget using JSCal2 from http://www.dynarch.com/projects/calendar/
'''

from django.utils.encoding import force_unicode
from django.conf import settings
from django import forms
import datetime, time
from django.utils.safestring import mark_safe

# DATETIMEWIDGET
calbtn = u'''<img src="%simages/calendar.gif" alt="calendar" id="%s_btn" style="cursor: pointer;" title="Select date" />
<script type="text/javascript">
	Calendar.setup({
		inputField     	:    "%s",
		dateFormat     	:    "%s",
		trigger        	:    "%s_btn",
		weekNumbers		:	false,
		bottomBar		:	false,
		fdow			:	0,
		min				: 	%s,
		max				:	%s,
	});
</script>'''

class DateTimeWidget(forms.widgets.TextInput):
	def __init__(self, attrs=None):
		default_attrs = {'min_date': '20000101', 'max_date': '20120101'}
		if attrs:
			default_attrs.update(attrs)
		super(forms.widgets.TextInput, self).__init__(default_attrs)

	class Media:
		css = {
			'all': (
				'calendar/css/jscal2.css',
				'calendar/css/border-radius.css',
				'calendar/css/steel/steel.css',
				)
		}
		js = (
			'calendar/js/jscal2.js',
			'calendar/js/lang/en.js',
			)

	dformat = '%Y-%m-%d'

	def render(self, name, value, attrs=None):
		if value is None: value = ''
		final_attrs = self.build_attrs(attrs, type=self.input_type, name=name)
		if value != '':
			try:
				final_attrs['value'] =\
				force_unicode(value.strftime(self.dformat))
			except:
				final_attrs['value'] =\
				force_unicode(value)
		if not final_attrs.has_key('id'):
			final_attrs['id'] = u'%s_id' % (name)
		id = final_attrs['id']

		jsdformat = self.dformat #.replace('%', '%%')
		cal = calbtn % (settings.STATIC_URL, id, id, jsdformat, id, final_attrs['min_date'], final_attrs['max_date'])
		a = u'<input%s />%s%s' % (forms.util.flatatt(final_attrs), self.media, cal)
		return mark_safe(a)

	def value_from_datadict(self, data, files, name):
		dtf = forms.fields.DEFAULT_DATETIME_INPUT_FORMATS
		empty_values = forms.fields.EMPTY_VALUES

		value = data.get(name, None)
		if value in empty_values:
			return None
		if isinstance(value, datetime.datetime):
			return value
		if isinstance(value, datetime.date):
			return datetime.datetime(value.year, value.month, value.day)
		for format in dtf:
			try:
				return datetime.datetime(*time.strptime(value, format)[:6])
			except ValueError:
				continue
		return None

	def _has_changed(self, initial, data):
		"""
				Return True if data differs from initial.
				Copy of parent's method, but modify value with strftime function before final comparsion
				"""
		if data is None:
			data_value = u''
		else:
			data_value = data

		if initial is None:
			initial_value = u''
		else:
			initial_value = initial

		try:
			if force_unicode(initial_value.strftime(self.dformat)) != force_unicode(data_value.strftime(self.dformat)):
				return True
		except:
			if force_unicode(initial_value) != force_unicode(data_value):
				return True

		return False
