from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse

from OpenGenomeBrowser.settings import GENOMIC_DATABASE
from website.models import Organism, Genome
from website.models.helpers.backup_file import read_file_or_default, overwrite_with_backup


class MarkdownObject:
    def __init__(self, type: str, name: str, file_path: str, featured_on: [str]):
        self.type = type
        self.name = name
        self.file_path = file_path
        self.featured_on = featured_on

    @property
    def markdown(self):
        return read_file_or_default(file=f'{GENOMIC_DATABASE}/{self.file_path}', default='')

    def set_markdown(self, md: str, user: str):
        self.obj.set_markdown(md=md, user=user)


class MarkdownObjectOrganism(MarkdownObject):
    def __init__(self, organism: str):
        self.obj = Organism.objects.get(name=organism)
        super().__init__(
            type='organism',
            name=self.obj.name,
            file_path=self.obj.markdown_path(relative=True),
            featured_on=[f'/organism/{self.obj.name}'] + [f'/genome/{i}' for i in self.obj.genome_set.values_list('identifier', flat=True)]
        )


class MarkdownObjectGenome(MarkdownObject):
    def __init__(self, genome: str):
        self.obj = Genome.objects.get(identifier=genome)
        super().__init__(
            type='genome',
            name=self.obj.identifier,
            file_path=self.obj.markdown_path(relative=True),
            featured_on=[f'/genome/{self.obj.identifier}']
        )


class MarkdownObjectPage(MarkdownObject):
    def __init__(self, page: str):
        self.page = page
        if not page == 'index':
            raise KeyError(f'Error: page does not exist: {page}.')
        super().__init__(
            type='page',
            name='index',
            file_path='index.md',
            featured_on=['/']
        )

    def set_markdown(self, md: str, user: str):
        from OpenGenomeBrowser.settings import GENOMIC_DATABASE
        overwrite_with_backup(
            file=f'{GENOMIC_DATABASE}/{self.file_path}',
            content=md,
            user=user,
            delete_if_empty=True
        )


def markdown_editor_view(request):
    context = dict(
        title='Markdown Editor',
        error_danger=[], error_warning=[], error_info=[],
        genomes=[],
        genome_to_species={}
    )

    try:
        if 'page' in request.GET:
            try:
                context['obj'] = MarkdownObjectPage(page=request.GET['page'])
            except KeyError as e:
                context['error_danger'].append(str(e))
        elif 'genome' in request.GET:
            context['obj'] = MarkdownObjectGenome(genome=request.GET['genome'])
        elif 'organism' in request.GET:
            context['obj'] = MarkdownObjectOrganism(organism=request.GET['organism'])
        else:
            context['error_danger'].append('Error: no page, genome or organism specified.')
    except ObjectDoesNotExist:
        context['error_danger'].append('Error: could not find object in database.')

    return render(request, 'admin/markdown-editor.html', context)


def markdown_editor_submit(request):
    type = request.POST['type']
    name = request.POST['name']
    markdown = request.POST['markdown']
    user = request.user.username

    if type == 'page':
        obj = MarkdownObjectPage(page=name)
    elif type == 'genome':
        obj = MarkdownObjectGenome(genome=name)
    elif type == 'organism':
        obj = MarkdownObjectOrganism(organism=name)
    else:
        return JsonResponse(dict(message='Type not supported!'), status=400)

    obj.set_markdown(md=markdown, user=user)

    return JsonResponse(dict(success=True))
