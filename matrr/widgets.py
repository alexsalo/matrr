from itertools import chain
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe
from django.utils.encoding import  force_unicode
from matrr.models import Availability, Monkey

from django.forms import CheckboxSelectMultiple, CheckboxInput

class CheckboxSelectMultipleLink(CheckboxSelectMultiple):
  def __init__(self, link_base, tissue, attrs=None, choices=()):
    self.tissue = tissue
    self.link_base = link_base
    super(CheckboxSelectMultipleLink, self).__init__(attrs, choices)
  
  
  def render(self, name, value, attrs=None, choices=()):
    if value is None: value = []
    has_id = attrs and 'id' in attrs
    final_attrs = self.build_attrs(attrs, name=name)
    output = [u'<ul style="list-style-type:none;">']
    # Normalize to strings
    str_values = set([force_unicode(v) for v in value])
    for i, (mky_id, mky_real_id) in enumerate(chain(self.choices, choices)):
      # If an ID attribute was given, add a numeric index as a suffix,
      # so that the checkboxes don't all have the same ID attribute.
      if has_id:
        final_attrs = dict(final_attrs, id='%s_%s' % (attrs['id'], i))
        label_for = u' for="%s"' % final_attrs['id']
      else:
        label_for = ''

      cb = CheckboxInput(final_attrs, check_test=lambda value: value in str_values)
      mky_id = force_unicode(mky_id)
      rendered_cb = cb.render(name, mky_id)
      mky_real_id = conditional_escape(force_unicode(mky_real_id))
      if self.tissue:
        monkey = Monkey.objects.get(mky_id=mky_id)
        availability = self.tissue.get_availability(monkey)
        if availability == Availability.Available:
          availability_str = 'Available'
        elif availability == Availability.In_Stock:
          availability_str = 'In Stock'
        elif availability == Availability.Unavailable:
          availability_str = 'Unavailable'

        if availability == Availability.Unavailable:
          output.append(u'<li><a href=\'%s%s\' onClick=\'javascript:window.open("%s%s");return false;\'>%s</a> Status: %s</li>' % ( self.link_base, mky_real_id, self.link_base, mky_real_id, mky_real_id, availability_str))
        else:
          output.append(u'<li><label%s>%s <a href=\'%s%s\' onClick=\'javascript:window.open("%s%s");return false;\'>%s</a></label>  Status: %s</li>' % (label_for, rendered_cb, self.link_base, mky_real_id, self.link_base, mky_real_id, mky_real_id, availability_str))
      else:
        # this is for custom tissue requests
        output.append(u'<li><label%s>%s <a href=\'%s%s\' onClick=\'javascript:window.open("%s%s");return false;\'>%s</a></label></li>' % (label_for, rendered_cb, self.link_base, mky_real_id, self.link_base, mky_real_id, mky_real_id))

    return mark_safe(u'\n'.join(output))

