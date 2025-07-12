from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def persian_number(value):
    """Convert English digits in a string or int to Persian digits."""
    persian_digits = '۰۱۲۳۴۵۶۷۸۹'
    return ''.join(persian_digits[int(ch)] if ch.isdigit() else ch for ch in str(value))

@register.filter
def intcomma_float(value, decimal_places=3):
    try:
        value = float(value)
    except (ValueError, TypeError):
        return value
    int_part, dot, frac_part = f"{value:.{decimal_places}f}".partition('.')
    int_part = "{:,}".format(int(int_part))
    frac_part = frac_part.rstrip('0')
    if frac_part:
        return f"{int_part}.{frac_part}"
    else:
        return int_part
