import os
from django.core.exceptions import ValidationError

def validate_excel_file(value):
    ext = os.path.splitext(value.name)[1]  # e.g. '.xlsx'
    valid_extensions = ['.xls', '.xlsx']
    if ext.lower() not in valid_extensions:
        raise ValidationError('Only Excel files (.xls or .xlsx) can be uploaded.')
