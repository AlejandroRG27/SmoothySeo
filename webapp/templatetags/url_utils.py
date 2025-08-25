from django import template
from urllib.parse import urljoin as urllib_urljoin

register = template.Library()

@register.filter
def url_join(base, path):
    return urllib_urljoin(base.rstrip('/') + '/', path.lstrip('/'))