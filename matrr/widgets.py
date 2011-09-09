from itertools import chain
from django.utils.html import escape, conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import  force_unicode
from matrr.models import Availability, Monkey
from django.forms.util import flatatt

from django.forms import *
from django.forms.widgets import Input
import re

class CheckboxSelectMultipleLink(CheckboxSelectMultiple):
  def __init__(self, link_base, tissue, attrs=None, choices=()):
    self.tissue = tissue
    self.link_base = link_base
    super(CheckboxSelectMultipleLink, self).__init__(attrs, choices)
  
  
  def render(self, name, value, attrs=None, choices=()):
    if value is None: value = []
    has_id = attrs and 'id' in attrs
    final_attrs = self.build_attrs(attrs, name=name)
    output = [u'<fieldset><legend><input type=\'checkbox\' id=\'%s\' onclick=\'toggle_checked(this, "%s")\'> <label for=\'%s\'>Select All Monkeys</label></legend>' % (attrs['id'], name, attrs['id'])]
    output.append(u'<ul style="list-style-type:none;">')
    # Normalize to strings
    str_values = set([force_unicode(v) for v in value])
    for i, (mky_id, mky_real_id) in enumerate(chain(self.choices, choices)):
      # If an ID attribute was given, add a numeric index as a suffix,
      # so that the checkboxes don't all have the same ID attribute.
      if has_id:
        final_attrs = dict(final_attrs,
                           id='%s_%s' % (attrs['id'], i),
                           onclick="check_toggler(document.getElementById('%s'), '%s')" % \
                                    (attrs['id'], name))
        label_for = u' for="%s"' % final_attrs['id']
      else:
        label_for = ''

      cb = CheckboxInput(final_attrs,
                         check_test=lambda value: value in str_values,)
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

      if self.tissue:
        availability = self.tissue.get_monkey_availability(monkey)
        if availability == Availability.Available:
          availability_str = 'Available'
        elif availability == Availability.In_Stock:
          availability_str = 'In Stock'
        elif availability == Availability.Unavailable:
          availability_str = 'Unavailable'

        if availability == Availability.Unavailable:
          output.append(u'<li><a href=\'%s%s\' onClick=\'javascript:window.open("%s%s");return false;\'><img src="/static/images/arrow_popup.png" width="8" height="8" style=\'vertical-align: text-top\' alt="external link"/>%s</a> Status: %s Assignment: %s</li>' % ( self.link_base,
                                     mky_real_id,
                                     self.link_base,
                                     mky_real_id,
                                     mky_real_id,
                                     availability_str,
                                     assignment,))
        else:
          output.append(u'<li><label%s>%s <a href=\'%s%s\' onClick=\'javascript:window.open("%s%s");return false;\'><img src="/static/images/arrow_popup.png" width="8" height="8" style=\'vertical-align: text-top\' alt="external link"/>%s</a></label>  Status: %s  Assignment: %s</li>' % (label_for,
                                                            rendered_cb,
                                                            self.link_base,
                                                            mky_real_id,
                                                            self.link_base,
                                                            mky_real_id,
                                                            mky_real_id,
                                                            availability_str,
                                                            assignment))
      else:
        # this is for custom tissue requests
        output.append(u'<li><label%s>%s <a href=\'%s%s\' onClick=\'javascript:window.open("%s%s");return false;\'><img src="/static/images/arrow_popup.png" width="8" height="8" style=\'vertical-align: text-top\' alt="external link"/>%s</a></label>  Assignment: %s</li>' % (label_for,
                                                rendered_cb,
                                                self.link_base,
                                                mky_real_id,
                                                self.link_base,
                                                mky_real_id,
                                                mky_real_id,
                                                assignment))
    output.append(u'</ul></fieldset>')
    output.append(u"<script type='text/javascript'>check_toggler(document.getElementById('%s'), '%s');</script>" % \
                                    (attrs['id'], name))
    return mark_safe(u'\n'.join(output))


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
    output = [u'<fieldset><legend><input type=\'checkbox\' id=\'%s\' onclick=\'toggle_checked(this, "%s")\'> <label for=\'%s\'>Select All Monkeys</label></legend>' % (attrs['id'], name, attrs['id'])]
    # Normalize to strings
    str_values = set([force_unicode(v) for v in value])
    for i, (mky_id, mky_real_id) in enumerate(chain(self.choices, choices)):
      # If an ID attribute was given, add a numeric index as a suffix,
      # so that the checkboxes don't all have the same ID attribute.
      if has_id:
        final_attrs = dict(final_attrs,
                           id='%s_%s' % (attrs['id'], i),
                           onclick="check_toggler(document.getElementById('%s'), '%s')" % \
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
      output.append(u'<label%s>%s <a href=\'%s\' onClick=\'javascript:window.open("%s");return false;\'><img src="/static/images/arrow_popup.png" width="8" height="8" style=\'vertical-align: text-top\' alt="external link"/>%s</a></label>' % \
                      (label_for,
                       rendered_cb,
                       link,
                       link,
                       mky_real_id))
    output.append(u'</fieldset>')
    return mark_safe(u'\n'.join(output))