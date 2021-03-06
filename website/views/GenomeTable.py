from django.shortcuts import render
from website.models import Genome
from .LoadTableScript import get_yadcf_columns
from OpenGenomeBrowser.settings import DEFAULT_GENOMES_COLUMNS

std = Genome.get_selector_to_description_dict()
default_columns = [(col, std[col]['description']) for col in DEFAULT_GENOMES_COLUMNS]


def genome_list_view(request):
    yadcf_columns = get_yadcf_columns()
    yadcf_columns = [(entry, yadcf_columns[entry]['description']) for entry in yadcf_columns]

    for entry in default_columns:
        yadcf_columns.remove(entry)

    context = dict(
        title='Genomes',
        yadcf_columns=yadcf_columns,
        default_columns=default_columns
    )
    return render(request, 'website/genome_table.html', context)
