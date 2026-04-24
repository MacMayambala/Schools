from django import template

register = template.Library()

@register.filter(name='dict_key')
def dict_key(dictionary, key):
    """Access dictionary values by dynamic key: dict|dict_key:key_var"""
    if dictionary:
        return dictionary.get(key)
    return None

@register.filter(name='get_item')
def get_item(dictionary, key):
    """Alias for dict_key, often used for student ID lookups"""
    return dict_key(dictionary, key)

@register.filter(name='grade_points')
def grade_points(grade):
    """Converts a grade string into a numeric point value"""
    points = {
        'D1': 1, 'D2': 2,
        'C3': 3, 'C4': 4, 'C5': 5, 'C6': 6,
        'P7': 7, 'P8': 8, 'F9': 9, 'F': 9
    }
    return points.get(str(grade).strip().upper(), '-')