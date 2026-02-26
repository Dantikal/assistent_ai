from django import template

register = template.Library()

@register.filter
def mul(value, arg):
    """Умножение двух чисел"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def div(value, arg):
    """Деление двух чисел"""
    try:
        if float(arg) == 0:
            return 0
        return float(value) / float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def percentage(value, total):
    """Вычисление процента"""
    try:
        if float(total) == 0:
            return 0
        return (float(value) / float(total)) * 100
    except (ValueError, TypeError):
        return 0

@register.filter
def replace(value, arg):
    """Замена подстроки в строке"""
    try:
        old, new = arg.split(':', 1)
        return str(value).replace(old, new)
    except (ValueError, AttributeError):
        return value

@register.filter
def slugify(value):
    """Преобразование строки в slug формат"""
    try:
        import re
        value = str(value).lower()
        value = re.sub(r'[^\w\s-]', '', value)
        value = re.sub(r'[-\s]+', '-', value)
        return value.strip('-')
    except:
        return str(value).lower().replace(' ', '-')
