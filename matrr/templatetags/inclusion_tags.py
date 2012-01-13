from django import template


register = template.Library()
@register.inclusion_tag("matrr/pagination.html", takes_context=False)
def pagination(object_list):
	return {'object_list': object_list}