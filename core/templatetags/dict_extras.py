from django import template
register = template.Library()

@register.filter
def dict_get(d, key):
    """Return the value from dictionary 'd' for the given key."""
    return d.get(key)