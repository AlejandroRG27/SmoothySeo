from django import template
from django.utils.safestring import mark_safe
import json
from urllib.parse import urlparse

register = template.Library()

@register.filter
def split(value, delimiter):
    return value.split(delimiter)

@register.filter
def trim(value):
    return value.strip()

@register.filter
def lookup(dictionary, key):
    if isinstance(dictionary, dict):
        return dictionary.get(key, '')  
    return '' 

@register.filter
def replace_underscore(value):
    if isinstance(value, str):
        return value.replace('_', ' ')
    return value

@register.filter
def to_json(value):
    return mark_safe(json.dumps(value, indent=2))

@register.filter
def is_dict(value):
    return isinstance(value, dict)

@register.filter
def is_list(value):
    return isinstance(value, list)

@register.filter
def items(value):
    return list(value.items()) if isinstance(value, dict) else []

@register.filter
def is_url(value):
    try:
        result = urlparse(str(value))
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

@register.filter
def is_valid_url(value):
    try:
        result = urlparse(value)
        return all([result.scheme, result.netloc])
    except ValueError:
        return False

@register.filter
def extract_relevant(value):
    if isinstance(value, dict):
        relevant = {}
        for k, v in value.items():
            if k.lower() in ['src', 'href', 'link', 'url', 'nodelabel', 'value']:
                relevant[k] = v
        return relevant
    elif isinstance(value, list):
        return [item for item in value if isinstance(item, dict) and any(k in item for k in ['nodelabel', 'value', 'url', 'src', 'href', 'link']) or is_url(item)]
    return value