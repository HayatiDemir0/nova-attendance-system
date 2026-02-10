from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Dictionary'den key ile değer al"""
    if dictionary is None:
        return None
    return dictionary.get(key)