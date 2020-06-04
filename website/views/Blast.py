import os
from django.shortcuts import render, HttpResponse, HttpResponseRedirect
from OpenGenomeBrowser import settings
from website.models.Genome import Genome
from django.conf import settings
# from dal import autocomplete
from django.http import HttpResponseBadRequest
from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from lib.ncbiblast.ncbi_blast.blast_wrapper import Blast

blast = Blast(system_blast=False, outfmt=5)

choice_to_settings = dict(
    blastn_ffn=dict(query_type='nucl', db_type='nucl', file_type='cds_ffn'),
    blastn_fna=dict(query_type='nucl', db_type='nucl', file_type='assembly_fasta'),
    blastp=dict(query_type='prot', db_type='prot', file_type='cds_faa'),
    blastx=dict(query_type='nucl', db_type='prot', file_type='cds_faa'),
    tblastn_ffn=dict(query_type='prot', db_type='nucl', file_type='cds_ffn'),
    tblastn_fna=dict(query_type='prot', db_type='nucl', file_type='assembly_fasta')
)


# https://django-autocomplete-light.readthedocs.io/en/master/tutorial.html
# class GenomeAutocomplete(autocomplete.Select2QuerySetView):
#     def get_queryset(self):
#         qs = Genome.objects.all()
#
#         if self.q:
#             qs = qs.filter(identifier__istartswith=self.q)
#
#         return qs


class BlastForm(forms.Form):
    class Meta:
        model = Genome
        fields = ('__all__')

    members = forms.CharField(widget=forms.Textarea(attrs={'cols': '40', 'rows': '1'}))

    blast_type = forms.ChoiceField(choices=[("blastp", "blastp: protein -> protein cds"),
                                            ("blastn_ffn", "blastn: nucleotides -> nucleotide cds"),
                                            ("blastn_fna", "blastn: nucleotides -> nucleotide assembly"),
                                            ("blastx", "blastx: nucleotides -> protein cds"),
                                            ("tblastn_ffn", "tblastn: protein -> nucleotide cds"),
                                            ("tblastn_fna", "tblastn: protein -> nucleotide assembly")])

    blast_input = forms.CharField(
        widget=forms.Textarea(attrs=({'style': 'font-family: Courier', 'spellcheck': 'false'})))

    def clean_members(self):
        """Turn comma separated identifier string into set of Genome objects"""
        members = set(self.cleaned_data['members'].split(','))
        found_members = set(Genome.objects.filter(identifier__in=members))
        if len(members) != len(found_members):
            raise ValidationError(_('Some members are invalid!'))
        return found_members


def blast_submit(request):
    print('blast-submit')
    if not request.method == 'POST':
        return HttpResponseBadRequest('Only POST requests allowed.')
    form = BlastForm(request.POST)
    if not form.is_valid():
        return HttpResponseBadRequest('Form is not valid!')

    cd = form.cleaned_data
    query = cd['blast_input']
    blast_type = cd['blast_type']
    query_type = choice_to_settings[blast_type]['query_type']
    db_type = choice_to_settings[blast_type]['db_type']
    blast_algorithm = cd['blast_type'].split('_')[0]

    file_type = choice_to_settings[blast_type]['file_type']

    fasta_files = [os.path.join(settings.GENOMIC_DATABASE_BN, getattr(genome.member, file_type)(relative=False))
                   for genome in cd['members']]

    print(blast_type, blast_algorithm, query_type, db_type, fasta_files)

    blast_output = blast.blast(fasta_string=query, db=fasta_files, mode=blast_algorithm)

    return HttpResponse(blast_output, content_type="text/plain")


def blast_view(request):
    context = dict(title='Blast')

    context['form'] = BlastForm()

    if 'members' in request.GET:
        key_members = request.GET['members'].split(' ')
        key_members = ','.join(key_members)
        context['form'] = BlastForm(dict(members=key_members, blast_type='blastp', blast_input='>'))
    else:
        context['form'] = BlastForm()

    return render(request, 'website/blast.html', context)
