from django import template

register = template.Library()

@register.filter
def get(d, key):
    return d[key]

@register.filter
def splitNameOnSpace(d):
	results = d.split(' ', 1)
	return '%s <strong>%s</strong>' % (results[1], results[0])

@register.filter
def di(d):
    return str(dir(d))