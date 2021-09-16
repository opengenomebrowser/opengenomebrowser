from django.shortcuts import render
from website.models.helpers.backup_file import read_file_or_default
from lib.ogb_cache.ogb_cache import ogb_cache, timedelta
from OpenGenomeBrowser.settings import LOGIN_REQUIRED, GENOMIC_DATABASE, CACHE_DIR, CACHE_MAXSIZE


def home_view(request):
    home_markdown = read_file_or_default(file=f'{GENOMIC_DATABASE}/index.md', default=None, default_if_empty=True)

    admin_actions = [
        dict(url='/admin/markdown-editor/?page=index', action='Edit markdown')
    ]

    credit = dict(
        People=[
            dict(
                name='Thomas Roder',
                img='/static/index/images/Thomas.jpg',
                img_cls='circle',
                role='PhD candidate',
                href='https://www.bioinformatics.unibe.ch/about_us/team/index_eng.html#person698529',
                did=['Code', 'Concept']
            ),
            dict(
                name='Simone Oberhänsli',
                img='/static/index/images/Simone.jpg',
                img_cls='circle',
                role='Staff scientist',
                href='https://www.bioinformatics.unibe.ch/about_us/team/index_eng.html#person649918',
                did=['Support', 'Ideas', 'Test data']
            ),
            dict(
                name='Noam Shani',
                img='/static/index/images/Noam.jpg',
                img_cls='circle',
                role='Agroscope Culture Collection',
                href='https://ira.agroscope.ch/en-US/Page/Mitarbeiter?agroscopeId=4823',
                did=['Support']
            ),
            dict(
                name='Rémy Bruggmann',
                img='/static/index/images/Remy.jpg',
                img_cls='circle',
                role='Supervisor, Head of IBU',
                href='https://www.bioinformatics.unibe.ch/about_us/team/index_eng.html#person156979',
                did=['Support', 'Infrastructure']
            ),
            dict(
                name='Darja Studer',
                img='/static/index/images/Darja.png',
                img_cls='circle',
                role='Designer',
                href='https://www.darjastuder.ch/',
                did=['Logo design']
            )
        ],

        Institutions=[
            dict(
                name='Interfaculty Bioinformatics Unit (IBU)',
                img='/static/index/images/unibe.png',
                img_cls='square',
                role='University of Bern',
                href='https://www.bioinformatics.unibe.ch/',
                did=['Infrastructure', 'Funding']
            ),
            dict(
                name='Agroscope',
                img='/static/index/images/agroscope.png',
                img_cls='square',
                role='Swiss center for agricultural research',
                href='https://www.agroscope.admin.ch/',
                did=['Funding']
            ),
            dict(
                name='Gebert Rüf Stiftung',
                img='/static/index/images/GRS.jpg',
                img_cls='circle',
                role='Grant-ID: GRS-070/17',
                href='https://www.grstiftung.ch/',
                did=['Funding']
            )
        ],

        Contact=[
            dict(
                name='GitHub Pages',
                img='/static/index/images/GitHubPages.jpg',
                img_cls='circle',
                role='Tutorials and Documentation',
                href='https://opengenomebrowser.github.io/opengenomebrowser/',
                did=[]
            ),
            dict(
                name='GitHub',
                img='/static/index/images/GitHub.svg',
                img_cls='square',
                role='Code repository',
                href='https://github.com/opengenomebrowser/opengenomebrowser/',
                did=[]
            ),
            dict(
                name='Discord',
                img='/static/index/images/Discord.svg',
                img_cls='square',
                role='Informal chat and support',
                href='https://discord.gg/mDm4fqf',
                did=[]
            )
        ],

        Software=[
            dict(
                name='OrthoFinder',
                img='/static/index/images/OrthoFinder.png',
                img_cls='circle',
                role='David Emms',
                href='https://github.com/davidemms/OrthoFinder/',
                did=['Orthologs', 'Core Genome Alignments']
            ),
            dict(
                name='GenDisCal / PaSit',
                img='/static/index/images/PaSiT.png',
                img_cls='square',
                role='Laboratory of Microbiology, Uni Gent',
                href='https://github.com/LM-UGent/GenDisCal/',
                did=['Calculation of pairwise assembly similarity']
            ),
            dict(
                name='DNA Features Viewer',
                img='/static/index/images/dna-features-viewer.png',
                img_cls='square',
                role='Edinburgh Genome Foundry',
                href='https://edinburgh-genome-foundry.github.io/DnaFeaturesViewer/',
                did=['Visualize gene loci']
            ),
            dict(
                name='Dot',
                img='/static/index/images/Dot.png',
                img_cls='square',
                role='Maria Nattestad',
                href='https://github.com/marianattestad/dot',
                did=['Dot plots']
            ),
            dict(
                name='TidyTree',
                img='/static/index/images/TidyTree.png',
                img_cls='circle',
                role='CDCgov',
                href='https://cdcgov.github.io/TidyTree/',
                did=['Visualisation of dendrograms']
            ),
            dict(
                name='National Center for Biotechnology Information',
                img='/static/index/images/ncbi.png',
                img_cls='circle',
                role='NCBI',
                href='https://blast.ncbi.nlm.nih.gov/Blast.cgi/',
                did=['BLAST alignment search', 'Taxonomy']
            ),
            dict(
                name='Blasterjs',
                img='/static/index/images/blasterjs.png',
                img_cls='circle',
                role='SING Group, University of Vigo',
                href='http://www.sing-group.org/blasterjs/',
                did=['Visualize BLAST results']
            ),
            dict(
                name='BioPython',
                img='/static/index/images/biopython.png',
                img_cls='square',
                role='Python library',
                href='https://biopython.org/',
                did=['Parsers', 'Wrappers']
            ),
            dict(
                name='Huey',
                img='/static/index/images/huey2.svg',
                img_cls='square',
                role='Python library',
                href='https://huey.readthedocs.io/',
                did=['Lightweight task queue']
            ),
            dict(
                name='Django',
                img='/static/index/images/Django.jpg',
                img_cls='circle',
                role='Python web framework',
                href='https://www.djangoproject.com/',
                did=['Web framework']
            )
        ]
    )

    context = dict(
        title='Home',
        no_help=True,
        credit=credit,
        home_markdown=home_markdown,
        admin_actions=admin_actions
    )

    if request.user.is_authenticated or not LOGIN_REQUIRED:
        try:
            sunburst_html, sunburst_js = sunburst()
            context['sunburst_html'] = sunburst_html
            context['sunburst_js'] = sunburst_js
        except AssertionError as e:
            context['error_warning'] = [str(e)]
        except Exception as e:
            context['error_danger'] = [f'Failed to load sunburst plot: {e}']

    return render(request, 'website/index.html', context)


def load_starburst_data():
    import pandas as pd
    from website.models import Organism, TaxID

    columns = ['taxsuperkingdom', 'taxphylum', 'taxclass', 'taxorder', 'taxfamily', 'taxgenus', 'taxspecies', 'taxsubspecies',
               'color', 'text_color_white']
    df = pd.DataFrame(Organism.objects.all().prefetch_related('taxid').values_list(*[f'taxid__{c}' for c in columns]), columns=columns)
    assert len(df) > 0, 'There are currently no organisms in the database.'
    df.fillna('-', inplace=True)
    colormap = {t: [c, w] for t, c, w in TaxID.objects.values_list('taxscientificname', 'color', 'text_color_white')}

    return df, columns[:-2], colormap


@ogb_cache(cache_root=CACHE_DIR, maxsize=CACHE_MAXSIZE, wait_tolerance=timedelta(seconds=10), invalid_after=timedelta(hours=24))
def sunburst():
    import json
    from io import StringIO
    import plotly.express as px

    df, columns, colormap = load_starburst_data()

    fig = px.sunburst(
        df,
        path=columns,
        color='color',
        color_discrete_map={c: f'rgb({c})' for t, (c, w) in colormap.items()}
    )
    fig.update_layout(autosize=False, uniformtext=dict(minsize=10, mode='hide'))
    fig.update_traces(hovertemplate="Superkingdom<br>%{label} (%{value})<extra></extra>")

    html = StringIO()
    fig.write_html(html, include_plotlyjs=False, full_html=False)
    html = html.getvalue()

    sunburst_id = html.split('<div id="', 1)[1].split('"', 1)[0]

    js = f'''
    const taxToCol = {json.dumps(colormap)};
    const sunburstId = {json.dumps(sunburst_id)};
    const sunburstColumns = {json.dumps(columns)};
    '''
    return html, js
