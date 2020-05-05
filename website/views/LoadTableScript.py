import json
from website.models import Tag, Member
from django.shortcuts import render
from lib.django_template_increment_counter import Counter

# prepare yadcf settings
selector_to_description_dict = Member.get_selector_to_description_dict()
tags = Tag.getTagList().__str__()

yadcf_columns = Member.get_selector_to_description_dict()

yadcf_settings = {
    'no-filter': {
        'column_defs': "{{{{title: '{description}', name: '{selector}', targets: {{counter}}}}}}",
    },
    'text': {
        'column_defs': "{{{{title: '{description}', name: '{selector}', targets: {{counter}}}}}}",
        'init': "{{{{column_number: {{counter}}, filter_type: 'text', filter_delay: 200}}}}",
    },
    'binary': {
        'column_defs': "{{{{title: '{description}', name: '{selector}', targets: {{counter}}}}}}",
        'init': "{{{{column_number: {{counter}}, data: ['True', 'False'], filter_default_label: ''}}}}"
    },
    'range_date': {
        'column_defs': "{{{{title: '{description}', name: '{selector}', targets: {{counter}}}}}}",
        'init': "{{{{column_number: {{counter}}, exclude: true, filter_type: 'range_date', date_format: 'yyyy-mm-dd', filter_delay: 500,}}}}",
    },
    'multi_select': {
        'column_defs': "{{{{title: '{description}', name: '{selector}', targets: {{counter}}}}}}",
        'init': "{{{{column_number: {{counter}}, filter_type: 'multi_select', select_type: 'select2'}}}}",
    },
    'custom-tags': {
        'column_defs': "{{{{title: '{description}', name: '{selector}', targets: {{counter}}}}}}",
        'init': "{{{{column_number: {{counter}}, filter_type: 'multi_select', select_type: 'select2', select_type_options: {{{{width: '150px', placeholder: 'Select tag', allowClear: true}}}}, column_data_type: 'html', html_data_type: 'text', data: {tags}}}}}"
    },
}

for selector in yadcf_columns:
    filter_type = yadcf_columns[selector]['filter_type']
    description = yadcf_columns[selector]['description']
    yadcf_columns[selector]['column_defs'] = yadcf_settings[filter_type]['column_defs'].format(selector=selector,
                                                                                               description=description,
                                                                                               counter='{counter}')
    if 'init' in yadcf_settings[filter_type]:
        yadcf_columns[selector]['init'] = yadcf_settings[filter_type]['init'].format(tags=tags)

    if selector == 'representative':
        yadcf_columns[selector]['ex_filter_column'] = "[{counter}, 'True']"
        yadcf_columns[selector]['init'] = yadcf_columns[selector]['init']
    if selector == 'contaminated':
        yadcf_columns[selector]['ex_filter_column'] = "[{counter}, 'False']"
        yadcf_columns[selector]['init'] = yadcf_columns[selector]['init']
    if selector == 'strain.restricted':
        yadcf_columns[selector]['ex_filter_column'] = "[{counter}, 'False']"
        yadcf_columns[selector]['init'] = yadcf_columns[selector]['init']


def render_script(request):
    columns = ["strain.name", "identifier", "strain.taxid.taxscientificname", "member_tags", "strain_tags"]  # default

    if 'columns' in request.GET:
        temp = json.loads(request.GET['columns'])
        if isinstance(temp, list) and len(temp) > 0 and all(isinstance(elem, str) for elem in temp):
            columns = temp

    yadcf_init, yadcf_column_defs, yadcf_ex_filter_column, indexes, tax_indexes = __generate_table_params(columns)

    context = {
        'yadcf_init': yadcf_init,
        'yadcf_column_defs': yadcf_column_defs,
        'yadcf_ex_filter_column': yadcf_ex_filter_column,
        'indexes': indexes,
        'tax_indexes': tax_indexes
    }
    return render(request, 'website/load_table_script.js', context)


def __generate_table_params(columns_to_show):
    # ToDo: add classes to identifier and strain to trigger right-click-menus (https://datatables.net/reference/option/columns.className)
    yadcf_column_defs = []
    yadcf_ex_filter_column = []
    yadcf_init = []

    index = {
        'representative': None,
        'contaminated': None,
        'strain.restricted': None
    }  # required to add stripes to table

    tax_indexes = []

    c = 0

    if 'representative' not in columns_to_show:
        yadcf_column_defs.append(
            yadcf_columns['representative']['column_defs'].format(counter=c)[:-1] + ", visible: false}")
        yadcf_init.append(yadcf_columns['representative']['init'].format(counter=c)[
                          :-1] + ", filter_container_id: 'external_filter_representative'}")
        yadcf_ex_filter_column.append(yadcf_columns['representative']['ex_filter_column'].format(counter=c))
        index['representative'] = c
        c = c + 1

    if 'contaminated' not in columns_to_show:
        yadcf_column_defs.append(
            yadcf_columns['contaminated']['column_defs'].format(counter=c)[:-1] + ", visible: false}")
        yadcf_init.append(yadcf_columns['contaminated']['init'].format(counter=c)[
                          :-1] + ", filter_container_id: 'external_filter_contaminated'}")
        yadcf_ex_filter_column.append(yadcf_columns['contaminated']['ex_filter_column'].format(counter=c))
        index['contaminated'] = c
        c = c + 1

    if 'strain.restricted' not in columns_to_show:
        yadcf_column_defs.append(
            yadcf_columns['strain.restricted']['column_defs'].format(counter=c)[:-1] + ", visible: false}")
        yadcf_init.append(yadcf_columns['strain.restricted']['init'].format(counter=c)[
                          :-1] + ", filter_container_id: 'external_filter_strain_restricted'}")
        yadcf_ex_filter_column.append(yadcf_columns['strain.restricted']['ex_filter_column'].format(counter=c))
        index['strain_restricted'] = c
        c = c + 1

    if 'identifier' not in columns_to_show:
        yadcf_column_defs.append(
            yadcf_columns['identifier']['column_defs'].format(counter=c)[:-1] + ", visible: false}")
        index['identifier'] = c
        c = c + 1

    if 'strain.name' not in columns_to_show:
        yadcf_column_defs.append(
            yadcf_columns['strain.name']['column_defs'].format(counter=c)[:-1] + ", visible: false}")
        index['strain.name'] = c
        c = c + 1

    tax_index_offset = c

    for column in columns_to_show:
        yadcf_column_defs.append(yadcf_columns[column]['column_defs'].format(counter=c))
        if 'ex_filter_column' in yadcf_columns[column]:
            yadcf_ex_filter_column.append(yadcf_columns[column]['ex_filter_column'].format(counter=c))
        if 'init' in yadcf_columns[column]:
            yadcf_init.append(yadcf_columns[column]['init'].format(counter=c))

        if column == 'representative':
            index['representative'] = c
        elif column == 'contaminated':
            index['contaminated'] = c
        elif column == 'strain.restricted':
            index['strain_restricted'] = c
        elif column == 'identifier':
            index['identifier'] = c
        elif column == 'strain.name':
            index['strain_name'] = c

        elif column.startswith("strain.taxid.tax"):
            tax_indexes.append((c-tax_index_offset, c))

        c = c + 1


    return ",\n".join(yadcf_init), ",\n".join(yadcf_column_defs), \
           ",\n".join(yadcf_ex_filter_column), index, tax_indexes


def get_yadcf_columns() -> dict:
    return yadcf_columns
