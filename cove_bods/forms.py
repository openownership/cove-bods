from django import forms
from django.conf import settings


class NewUploadForm(forms.Form):
    file_field_names = ["file_upload"]
    file_upload = forms.FileField(
        widget=forms.FileInput(
            attrs={
                "accept": ",".join(
                    settings.ALLOWED_JSON_CONTENT_TYPES
                    + settings.ALLOWED_JSON_EXTENSIONS
                    + settings.ALLOWED_SPREADSHEET_CONTENT_TYPES
                    + settings.ALLOWED_SPREADSHEET_EXTENSIONS
                )
            }
        ),
        label="",
    )
    sample_mode = forms.BooleanField(label="Process using Sample mode (see information above)", required=False)


class NewTextForm(forms.Form):
    file_field_names = []
    paste = forms.CharField(label="Paste (JSON only)", widget=forms.Textarea)
    sample_mode = forms.BooleanField(label="Process using Sample mode (see information above)", required=False)


class NewURLForm(forms.Form):
    file_field_names = []
    url = forms.URLField(label="URL")
    sample_mode = forms.BooleanField(label="Process using Sample mode (see information above)", required=False)
