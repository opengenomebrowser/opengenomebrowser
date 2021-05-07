from OpenGenomeBrowser.settings import GENOMIC_DATABASE
from website.models import Organism, Genome
from website.models.helpers.backup_file import read_file_or_default, overwrite_with_backup


class MarkdownObject:
    def __init__(self, type: str, name: str, file_path: str, featured_on: str):
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
            featured_on=f'/organism/{self.obj.name}'
        )


class MarkdownObjectGenome(MarkdownObject):
    def __init__(self, genome: str):
        self.obj = Genome.objects.get(identifier=genome)
        super().__init__(
            type='genome',
            name=self.obj.identifier,
            file_path=self.obj.markdown_path(relative=True),
            featured_on=f'/genome/{self.obj.identifier}'
        )


class MarkdownObjectPage(MarkdownObject):
    def __init__(self, page: str):
        self.page = page
        if page == 'index':
            super().__init__(
                type='page',
                name='index',
                file_path='/index.md',
                featured_on='/'
            )
        else:
            raise KeyError(f'Error: page does not exist: {page}.')

    def set_markdown(self, md: str, user: str):
        from OpenGenomeBrowser.settings import GENOMIC_DATABASE
        overwrite_with_backup(
            file=f'{GENOMIC_DATABASE}/{self.file_path}',
            content=md,
            user=user,
            delete_if_empty=True
        )
