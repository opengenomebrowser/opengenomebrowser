from django.shortcuts import render
from website.models import Member
from .LoadTableScript import get_yadcf_columns

default_columns = ["strain.name", "identifier", "strain.taxid.taxscientificname", "member_tags", "strain_tags"]
std = Member.get_selector_to_description_dict()
default_columns = [(col, std[col]['description']) for col in default_columns]


def member_list_view(request):
    yadcf_columns = get_yadcf_columns()
    yadcf_columns = [(entry, yadcf_columns[entry]['description']) for entry in yadcf_columns]

    for entry in default_columns:
        yadcf_columns.remove(entry)

    context = {
        'yadcf_columns': yadcf_columns,
        'default_columns': default_columns
    }
    return render(request, 'website/member_table.html', context)
