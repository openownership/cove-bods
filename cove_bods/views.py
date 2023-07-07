import logging

from cove_project import settings
from django.shortcuts import render
from libcoveweb2.views import (
    ExploreDataView,
    InputDataView
)
from libcoveweb2.models import SuppliedDataFile
from cove_bods.forms import NewTextForm, NewUploadForm, NewURLForm


logger = logging.getLogger(__name__)


JSON_FORM_CLASSES = {
        "upload_form": NewUploadForm,
        "text_form": NewTextForm,
        "url_form": NewURLForm,
    }


class NewInput(InputDataView):
    form_classes = JSON_FORM_CLASSES
    input_template = "cove_bods/index.html"
    allowed_content_types = settings.ALLOWED_JSON_CONTENT_TYPES + settings.ALLOWED_SPREADSHEET_CONTENT_TYPES
    content_type_incorrect_message = "This does not appear to be a supported file."
    allowed_file_extensions = settings.ALLOWED_JSON_EXTENSIONS + settings.ALLOWED_SPREADSHEET_EXTENSIONS
    file_extension_incorrect_message = "This does not appear to be a supported file."
    supplied_data_format = "unknown"

    def get_active_form_key(self, forms, request_data):
        if "paste" in request_data:
            return "text_form"
        elif "url" in request_data:
            return "url_form"
        else:
            return "upload_form"

    def save_file_content_to_supplied_data(
        self, form_name, form, request, supplied_data
    ):
        if form.cleaned_data["sample_mode"]:
            supplied_data.meta["sample_mode"] = True
            supplied_data.save()
        if form_name == "upload_form":
            supplied_data.save_file(request.FILES["file_upload"])
        elif form_name == "text_form":
            supplied_data.save_file_contents(
                "input.json",
                form.cleaned_data["paste"],
                "application/json",
                None
            )
        elif form_name == "url_form":
            supplied_data.save_file_from_source_url(
                form.cleaned_data["url"], content_type="application/json"
            )


def index(request):

    forms = {
        "json": {
            form_name: form_class()
            for form_name, form_class in JSON_FORM_CLASSES.items()
        },
    }

    return render(request, "cove_bods/index.html", {"forms": forms})


class ExploreBODSView(ExploreDataView):
    explore_template = "cove_bods/explore.html"
    processing_template = "cove_bods/processing.html"
    error_template = "cove_bods/error.html"

    def default_explore_context(self, supplied_data):
        return {
            # Misc
            "supplied_data_files": SuppliedDataFile.objects.filter(
                supplied_data=supplied_data
            ),
        }
