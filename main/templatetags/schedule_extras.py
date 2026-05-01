from django import template


register = template.Library()


@register.filter
def dict_get(value, key):
    """
    Safe dict lookup in templates.
    Returns [] if key is missing.
    """
    if not isinstance(value, dict):
        return []
    return value.get(key, [])

