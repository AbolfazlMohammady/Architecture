from django.core.exceptions import ValidationError

def validate_national_code(value):
    if not value.isdigit():
        raise ValidationError("only degit allowed.")
    if len(value) != 10:
        raise ValidationError("lenth must be 10 digit.")
