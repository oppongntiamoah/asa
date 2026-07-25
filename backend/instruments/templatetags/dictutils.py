"""Dynamic-key dict lookup — Django templates only support `dict.key` for a
literal key, not a loop variable, so a filter is the standard way to do
`{{ some_dict|dict_get:loop_var }}`."""
from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    return d.get(key) if d else None
