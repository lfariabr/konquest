# core/resolvers/clean_phone_number.py

def clean_phone_number(number):
    cleaned = ''.join(filter(lambda x: x.isdigit() or x == '+', str(number)))
    if cleaned.startswith('55'):
        return cleaned[2:] if len(cleaned) > 11 else cleaned
    return cleaned