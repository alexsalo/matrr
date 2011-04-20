from itertools import chain
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import  force_unicode

from django.forms import CheckboxSelectMultiple, CheckboxInput

class CheckboxSelectMultipleLink(CheckboxSelectMultiple):
  def __init__(self, link_base, attrs=None, choices=()):
    self.link_base = link_base
    super(CheckboxSelectMultipleLink, self).__init__(attrs, choices)
  
  
  def render(self, name, value, attrs=None, choices=()):
    if value is None: value = []
    has_id = attrs and 'id' in attrs
    final_attrs = self.build_attrs(attrs, name=name)
    output = [u'<ul style="list-style-type:none;">']
    # Normalize to strings
    str_values = set([force_unicode(v) for v in value])
    for i, (option_value, option_label) in enumerate(chain(self.choices, choices)):
      # If an ID attribute was given, add a numeric index as a suffix,
      # so that the checkboxes don't all have the same ID attribute.
      if has_id:
        final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
        label_for = u' for="%s"' % final_attrs['id']
      else:
        label_for = ''

      cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
      option_value = force_unicode(option_value)
      rendered_cb = cb.render(name, option_value)
      option_label = conditional_escape(force_unicode(option_label))
      output.append(u'<li><label%s>%s <a href=\'%s%s\' onClick=\'javascript:window.open("%s%s");return false;\'>%s</a></label></li>' % (label_for, rendered_cb, self.link_base, option_label, self.link_base, option_label, option_label))
    output.append(u'</ul>')
    return mark_safe(u'\n'.join(output))

