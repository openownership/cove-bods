from django.core.files.base import ContentFile
from django.core.files.storage import default_storage

from libcovebods.schema import SchemaBODS
from libcovebods.config import LibCoveBODSConfig
from libcovebods.jsonschemavalidate import JSONSchemaValidator
from libcovebods.additionalfields import AdditionalFields
import libcovebods.run_tasks
import libcovebods.data_reader
from typing import List

import json
import os.path

import flattentool
from sentry_sdk import capture_exception

from libcoveweb2.models import SuppliedDataFile, SuppliedData
from libcoveweb2.process.base import ProcessDataTask
from libcoveweb2.process.common_tasks.task_with_state import TaskWithState

# from libcove.lib.converters import convert_json, convert_spreadsheet
from libcoveweb2.utils import get_file_type_for_flatten_tool
from libcoveweb2.utils import group_data_list_by


def create_error_file(name: str, id: str, data: dict):
    """Create temporary error file"""
    filename = f"{name}-{id}-error.json"
    default_storage.save(filename, ContentFile(json.dumps(data).encode('utf-8')))


def error_file_exists(name: str, id: str) -> bool:
    """Test if error file exists"""
    filename = f"{name}-{id}-error.json"
    return default_storage.exists(filename)


def read_error_file(name: str, id: str) -> dict:
    """Read data from error file"""
    filename = f"{name}-{id}-error.json"
    return json.loads(default_storage.open(filename).read().decode('utf-8'))


def delete_error_file(name: str, id: str):
    """Delete temporary error file"""
    filename = f"{name}-{id}-error.json"
    default_storage.delete(filename)


class Sample(ProcessDataTask):
    def is_processing_applicable(self) -> bool:
        return True

    def process(self, process_data: dict) -> dict:
        process_data["sample_mode"] = self.supplied_data.meta.get("sample_mode")
        return process_data

    def get_context(self):
        return {"sample_mode": self.supplied_data.meta.get("sample_mode")}


class SetOrTestSuppliedDataFormat(ProcessDataTask):

    map_file_type_to_format = {
        'json': 'json',
        'xlsx': 'spreadsheet',
        'ods': 'spreadsheet'
    }

    def is_processing_applicable(self) -> bool:
        return True

    def is_processing_needed(self) -> bool:
        return self.supplied_data.format == "unknown"

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format == "unknown":
            # Look up what data format is, and set it
            supplied_data_files = SuppliedDataFile.objects.filter(
                supplied_data=self.supplied_data
            )
            all_file_types = [get_file_type_for_flatten_tool(i) for i in supplied_data_files]
            file_types_reduced = list(set([i for i in all_file_types if i]))
            if len(file_types_reduced) == 1:
                self.supplied_data.format = self.map_file_type_to_format[file_types_reduced[0]]
                self.supplied_data.save()

            elif len(file_types_reduced) == 0:
                raise NotImplementedError("GOT ZERO")
                # TODO

            elif len(file_types_reduced) > 1:
                raise NotImplementedError("GOT MORE THAN ONE")
                # TODO

        return process_data

    def get_context(self):
        return {"original_format": self.supplied_data.format}


class WasJSONUploaded(ProcessDataTask):
    """Did user upload JSON?
    Then we don't actually have to do anything, but we want to save info about that JSON for later steps."""

    def is_processing_applicable(self) -> bool:
        return True

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format != "json":
            return process_data

        supplied_data_json_files = SuppliedDataFile.objects.filter(
            supplied_data=self.supplied_data, content_type="application/json"
        )
        if supplied_data_json_files.count() == 1:
            process_data[
                "json_data_filename"
            ] = supplied_data_json_files.first().upload_dir_and_filename()
        else:
            raise Exception("Can't find JSON original data!")

        return process_data

    def get_context(self):
        return {}


CONVERT_SPREADSHEET_INTO_JSON_DIR_NAME = "unflatten"


class ConvertSpreadsheetIntoJSON(ProcessDataTask):
    """If User uploaded Spreadsheet, convert to our primary format, JSON."""

    def __init__(
        self, supplied_data: SuppliedData, supplied_data_files: List[SuppliedDataFile]
    ):
        super().__init__(supplied_data, supplied_data_files)
        self.data_filename = os.path.join(
            self.supplied_data.data_dir(),
            CONVERT_SPREADSHEET_INTO_JSON_DIR_NAME,
            "unflattened.json",
        )

    def is_processing_applicable(self) -> bool:
        return self.supplied_data.format == "spreadsheet"

    def is_processing_needed(self) -> bool:
        return self.supplied_data.format == "spreadsheet" and not os.path.exists(
            self.data_filename
        )

    def process(self, process_data: dict) -> dict:
        if self.supplied_data.format != "spreadsheet":
            return process_data

        process_data["json_data_filename"] = self.data_filename

        # check already done
        if os.path.exists(self.data_filename):
            return process_data

        supplied_data_json_files = SuppliedDataFile.objects.filter(
            supplied_data=self.supplied_data
        )
        if supplied_data_json_files.count() != 1:
            raise Exception("Can't find Spreadsheet original data!")

        supplied_data_json_file = supplied_data_json_files.first()
        input_filename = supplied_data_json_file.upload_dir_and_filename()

        output_dir = os.path.join(
            self.supplied_data.data_dir(), CONVERT_SPREADSHEET_INTO_JSON_DIR_NAME
        )

        os.makedirs(output_dir, exist_ok=True)

        # We don't know what schema version the spreadsheet is in. Use default schema.
        schema = SchemaBODS()

        unflatten_kwargs = {
            "output_name": os.path.join(output_dir, "unflattened.json"),
            "root_list_path": "there-is-no-root-list-path",
            "root_id": "statementID",
            "id_name": "statementID",
            "root_is_list": True,
            "input_format": get_file_type_for_flatten_tool(supplied_data_json_file),
            "schema": schema.pkg_schema_url,
        }

        flattentool.unflatten(input_filename, **unflatten_kwargs)

        return process_data

    def get_context(self):
        context = {}
        # original format
        if self.supplied_data.format == "spreadsheet":
            context["original_format"] = "spreadsheet"
            # Download data
            if os.path.exists(self.data_filename):
                context["can_download_json"] = True
                context["download_json_url"] = os.path.join(
                    self.supplied_data.data_url(),
                    CONVERT_SPREADSHEET_INTO_JSON_DIR_NAME,
                    "unflattened.json",
                )
                context["download_json_size"] = os.stat(self.data_filename).st_size
            else:
                context["can_download_json"] = False
        # Return
        return context


class GetDataReaderAndConfigAndSchema(ProcessDataTask):
    def __init__(
        self, supplied_data: SuppliedData, supplied_data_files: List[SuppliedDataFile]
    ):
        super().__init__(supplied_data, supplied_data_files)
        self.data_filename = os.path.join(
            self.supplied_data.data_dir(), "schema.json"
        )

    def is_processing_applicable(self) -> bool:
        return True

    def is_processing_needed(self) -> bool:
        return False

    def process(self, process_data: dict) -> dict:
        # Make things and set info for later in processing
        process_data['data_reader'] = libcovebods.data_reader.DataReader(
            process_data["json_data_filename"], sample_mode=process_data['sample_mode']
        )
        process_data['config'] = LibCoveBODSConfig()
        process_data['schema'] = SchemaBODS(process_data['data_reader'], process_data['config'])
        # Save some to disk for templates
        if not os.path.exists(self.data_filename):
            save_data = {
                "schema_version_used": process_data['schema'].schema_version
            }
            with open(self.data_filename, "w") as fp:
                json.dump(save_data, fp, indent=4)
        # return
        return process_data

    def get_context(self):
        context = {}
        # data
        if os.path.exists(self.data_filename):
            with open(self.data_filename) as fp:
                context.update(json.load(fp))
        # done!
        return context


CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME = "flatten"


class ConvertJSONIntoSpreadsheets(ProcessDataTask):
    """Convert primary format (JSON) to spreadsheets"""

    def __init__(
        self, supplied_data: SuppliedData, supplied_data_files: List[SuppliedDataFile]
    ):
        super().__init__(supplied_data, supplied_data_files)
        self.output_dir = os.path.join(
            self.supplied_data.data_dir(),
            CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME,
            "data",
        )
        self.xlsx_filename = os.path.join(
            self.supplied_data.data_dir(),
            CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME,
            "data.xlsx",
        )
        self.data_id = str(self.supplied_data.id)

    def is_processing_applicable(self) -> bool:
        return True

    def is_processing_needed(self) -> bool:
        if os.path.exists(self.xlsx_filename):
            return False
        if error_file_exists("ConvertJSONIntoSpreadsheets", self.data_id):
            return False
        return True

    def process(self, process_data: dict) -> dict:

        # don't run if already done
        if os.path.exists(self.xlsx_filename):
            return process_data

        os.makedirs(self.output_dir, exist_ok=True)

        flatten_kwargs = {
            "output_name": self.output_dir,
            "root_list_path": "there-is-no-root-list-path",
            "root_id": "statementID",
            "id_name": "statementID",
            "root_is_list": True,
            "schema": process_data['schema'].pkg_schema_url,
        }

        try:
            flattentool.flatten(process_data["json_data_filename"], **flatten_kwargs)
        except Exception as err:
            capture_exception(err)
            create_error_file("ConvertJSONIntoSpreadsheets", self.data_id,
                              {"type": type(err).__name__,
                               "filename": process_data["json_data_filename"].split('/')[-1]})

        return process_data

    def get_context(self):
        context = {}
        # XLSX
        if os.path.exists(self.xlsx_filename):
            context["can_download_xlsx"] = True
            context["download_xlsx_url"] = os.path.join(
                self.supplied_data.data_url(),
                CONVERT_JSON_INTO_SPREADSHEETS_DIR_NAME,
                "data.xlsx",
            )
            context["download_xlsx_size"] = os.stat(self.xlsx_filename).st_size
        else:
            context["can_download_xlsx"] = False
            if error_file_exists("ConvertJSONIntoSpreadsheets", self.data_id):
                context["xlsx_error"] = read_error_file("ConvertJSONIntoSpreadsheets", self.data_id)
                delete_error_file("ConvertJSONIntoSpreadsheets", self.data_id)
            else:
                context["xlsx_error"] = False
        # done!
        return context


class PythonValidateTask(TaskWithState):

    state_filename: str = "python_validate.json"

    def process_get_state(self, process_data: dict) -> dict:
        context = libcovebods.run_tasks.process_additional_checks(
            process_data['data_reader'],
            process_data['config'],
            process_data['schema'],
            task_classes=libcovebods.run_tasks.TASK_CLASSES_IN_SAMPLE_MODE if
            process_data["sample_mode"] else libcovebods.run_tasks.TASK_CLASSES
        )

        # counts
        context["additional_checks_count"] = len(context["additional_checks"])

        # We need to calculate some stats for showing in the view
        total_ownership_or_control_interest_statements = 0
        for key, count in \
                context['statistics']['count_ownership_or_control_statement_interest_statement_types'].items():
            total_ownership_or_control_interest_statements += count
        context['statistics'][
            'count_ownership_or_control_interest_statement'] = total_ownership_or_control_interest_statements  # noqa

        # The use of r_e_type is to stop flake8 complaining about line length
        r_e_type = 'registeredEntity'
        context['statistics']['count_entities_registeredEntity_legalEntity_with_any_identifier'] = (
                context['statistics']['count_entity_statements_types_with_any_identifier'][r_e_type] +
                context['statistics']['count_entity_statements_types_with_any_identifier']['legalEntity'])
        context['statistics']['count_entities_registeredEntity_legalEntity_with_any_identifier_with_id_and_scheme'] = (
                context['statistics']['count_entity_statements_types_with_any_identifier_with_id_and_scheme'][
                    r_e_type] +
                context['statistics']['count_entity_statements_types_with_any_identifier_with_id_and_scheme'][
                    'legalEntity'])
        context['statistics']['count_entities_registeredEntity_legalEntity'] = (
                context['statistics']['count_entity_statements_types'][r_e_type] +
                context['statistics']['count_entity_statements_types']['legalEntity'])
        unknown_schema_version_used = \
            [i for i in context['additional_checks'] if i['type'] == 'unknown_schema_version_used']
        context['unknown_schema_version_used'] = unknown_schema_version_used[0] \
            if unknown_schema_version_used else None
        context['inconsistent_schema_version_used_count'] = \
            len([i for i in context['additional_checks'] if i['type'] == 'inconsistent_schema_version_used'])

        context['checks_not_run_in_sample_mode'] = []
        if process_data["sample_mode"]:
            classes_not_run_in_sample_mode = [
                x for x in libcovebods.run_tasks.TASK_CLASSES
                if x not in libcovebods.run_tasks.TASK_CLASSES_IN_SAMPLE_MODE
            ]
            for class_not_run_in_sample_mode in classes_not_run_in_sample_mode:
                context['checks_not_run_in_sample_mode'].extend(
                    class_not_run_in_sample_mode.get_additional_check_types_possible(
                        process_data['config'],
                        process_data['schema']
                    )
                )
            context['checks_not_run_in_sample_mode'] = list(set(context['checks_not_run_in_sample_mode']))

        return context, process_data


class JsonSchemaValidateTask(TaskWithState):

    state_filename: str = "jsonschema_validate.json"

    def process_get_state(self, process_data: dict) -> dict:
        worker = JSONSchemaValidator(process_data['schema'])

        # Get list of validation errors
        validation_errors = worker.validate(process_data['data_reader'])
        validation_errors = [i.json() for i in validation_errors]

        # Context
        context = {
            "validation_errors_count": len(validation_errors),
            "validation_errors": group_data_list_by(
                validation_errors, lambda i: i["validator"] + str(i['path_ending']) + i["message"]
            )
        }

        return context, process_data


class AdditionalFieldsChecksTask(TaskWithState):

    state_filename: str = "additional_fields.json"

    def process_get_state(self, process_data: dict) -> dict:
        worker = AdditionalFields(process_data['schema'])

        output = worker.process(process_data['data_reader'])
        context = {"additional_fields": output}
        context["any_additional_fields_exist"] = len(output) > 0

        return context, process_data
