# forms.py
from django import forms

class ContactCsvUploadForm(forms.Form):
    csv_file = forms.FileField()