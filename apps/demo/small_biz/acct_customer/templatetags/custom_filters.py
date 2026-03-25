from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Allows accessing dictionary keys dynamically in templates"""
    return dictionary.get(key)