import json
import logging
import functools
import datetime
from decimal import Decimal

from django.shortcuts import render
from django.utils.translation import ugettext_lazy as _
from django.utils.html import format_html

from libcovebods.common_checks import common_checks_bods
from libcovebods.schema import SchemaBODS
from libcovebods.config import LibCoveBODSConfig
from libcove.lib.exceptions import CoveInputDataError
from cove.views import explore_data_context
from libcove.lib.converters import convert_spreadsheet, convert_json
from cove_project import settings

logger = logging.getLogger(__name__)


def cove_web_input_error(func):
    @functools.wraps(func)
    def wrapper(request, *args, **kwargs):
        try:
            return func(request, *args, **kwargs)
        except CoveInputDataError as err:
            return render(request, 'error.html', context=err.context)
    return wrapper


@cove_web_input_error
def explore_bods(request, pk):
    context, db_data, error = explore_data_context(request, pk)
    if error:
        return error

    lib_cove_bods_config = LibCoveBODSConfig()
    lib_cove_bods_config.config['root_list_path'] = settings.COVE_CONFIG['root_list_path']
    lib_cove_bods_config.config['root_id'] = settings.COVE_CONFIG['root_id']
    lib_cove_bods_config.config['id_name'] = settings.COVE_CONFIG['id_name']
    lib_cove_bods_config.config['root_is_list'] = settings.COVE_CONFIG['root_is_list']
    lib_cove_bods_config.config['bods_additional_checks_person_birthdate_max_year'] = datetime.datetime.now().year
    lib_cove_bods_config.config['bods_additional_checks_person_birthdate_min_year'] = \
        datetime.datetime.now().year - 120

    upload_dir = db_data.upload_dir()
    upload_url = db_data.upload_url()
    file_name = db_data.original_file.file.name
    file_type = context['file_type']

    if file_type == 'json':
        # open the data first so we can inspect for record package
        with open(file_name, encoding='utf-8') as fp:
            try:
                json_data = json.load(fp, parse_float=Decimal)
            except ValueError as err:
                raise CoveInputDataError(context={
                    'sub_title': _("Sorry, we can't process that data"),
                    'link': 'index',
                    'link_text': _('Try Again'),
                    'msg': _(format_html('We think you tried to upload a JSON file, but it is not well formed JSON.'
                                         '\n\n<span class="glyphicon glyphicon-exclamation-sign" aria-hidden="true">'
                                         '</span> <strong>Error message:</strong> {}', err)),
                    'error': format(err)
                })

            if not isinstance(json_data, list):
                raise CoveInputDataError(context={
                    'sub_title': _("Sorry, we can't process that data"),
                    'link': 'index',
                    'link_text': _('Try Again'),
                    'msg': _('BODS JSON should have a list as the top level, the JSON you supplied does not.'),
                })

        schema_bods = SchemaBODS(lib_cove_bods_config=lib_cove_bods_config)

        context.update(convert_json(upload_dir, upload_url, file_name, lib_cove_bods_config,
                                    schema_url=schema_bods.release_pkg_schema_url, replace=True,
                                    request=request, flatten=True))

    else:

        schema_bods = SchemaBODS(lib_cove_bods_config=lib_cove_bods_config)
        context.update(convert_spreadsheet(upload_dir, upload_url, file_name, file_type, lib_cove_bods_config,
                                           schema_url=schema_bods.release_pkg_schema_url))
        with open(context['converted_path'], encoding='utf-8') as fp:
            json_data = json.load(fp, parse_float=Decimal)

    context = common_checks_bods(context, upload_dir, json_data, schema_bods,
                                 lib_cove_bods_config=lib_cove_bods_config)

    if not db_data.rendered:
        db_data.rendered = True
    db_data.save()

    # We need to calculate some stats for showing in the view
    total_ownership_or_control_interest_statements = 0
    for key, count in context['statistics']['count_ownership_or_control_statement_interest_statement_types'].items():
        total_ownership_or_control_interest_statements += count
    context['statistics']['count_ownership_or_control_interest_statement'] = total_ownership_or_control_interest_statements # noqa

    # The use of r_e_type is to stop flake8 complaining about line length
    r_e_type = 'registeredEntity'
    context['statistics']['count_entities_registeredEntity_legalEntity_with_any_identifier'] = (
        context['statistics']['count_entity_statements_types_with_any_identifier'][r_e_type] +
        context['statistics']['count_entity_statements_types_with_any_identifier']['legalEntity'])
    context['statistics']['count_entities_registeredEntity_legalEntity_with_any_identifier_with_id_and_scheme'] = (
        context['statistics']['count_entity_statements_types_with_any_identifier_with_id_and_scheme'][r_e_type] +
        context['statistics']['count_entity_statements_types_with_any_identifier_with_id_and_scheme']['legalEntity'])
    context['statistics']['count_entities_registeredEntity_legalEntity'] = (
        context['statistics']['count_entity_statements_types'][r_e_type] +
        context['statistics']['count_entity_statements_types']['legalEntity'])

    template = 'cove_bods/explore.html'

    return render(request, template, context)
