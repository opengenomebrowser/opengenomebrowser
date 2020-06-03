from django.shortcuts import render, HttpResponse

from website.models.KeggMap import KeggMap


def index_view(request):
    personen = [
        dict(
            name='Thomas Roder',
            img='/static/index/images/Thomas.jpg',
            img_cls='circle',
            role='PhD student',
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
            name='Rémy Bruggmann',
            img='/static/index/images/Remy.jpg',
            img_cls='circle',
            role='Supervisor',
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
    ]

    institutions = [
        dict(
            name='Gebert Rüf Stiftung',
            img='/static/index/images/GRS.jpg',
            img_cls='circle',
            role='Grant-ID: GRS-070/17',
            href='https://www.grstiftung.ch/',
            did=['Funding']
        ),
        dict(
            name='Interfaculty Bioinformatics Unit',
            img='/static/index/images/unibe.png',
            img_cls='square',
            role='University of Bern',
            href='https://www.bioinformatics.unibe.ch/',
            did=['Infrastructure']
        ),
        dict(
            name='Agroscope',
            img='/static/index/images/agroscope.png',
            img_cls='square',
            role='Swiss center for agricultural research',
            href='https://www.agroscope.admin.ch/',
            did=['Infrastructure']
        )
    ]

    software = [
        dict(
            name='OrthoFinder',
            img='/static/index/images/OrthoFinder.png',
            img_cls='circle',
            role='David Emms',
            href='https://github.com/davidemms/OrthoFinder/',
            did=['Orthologs', 'Core Genome Alignments']
        ),
        dict(
            name='ChunLab\'s OAT',
            img='/static/index/images/OAT.svg',
            img_cls='square',
            role='CDCgov',
            href='https://www.ezbiocloud.net/tools/orthoani/',
            did=['Calculation of average nucleotide identity between assemblies']
        ),
        dict(
            name='Kyoto Enzyclopedia of Genes',
            img='/static/index/images/kegg.png',
            img_cls='square',
            role='square',
            href='https://www.kegg.jp/',
            did=['Pathway maps']
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
            name='DNA Features Viewer',
            img='/static/index/images/dna-features-viewer.png',
            img_cls='square',
            role='Edinburgh Genome Foundry',
            href='https://edinburgh-genome-foundry.github.io/DnaFeaturesViewer/',
            did=['Visualize gene loci']
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

    context = dict(
        credits_personen=personen,
        credits_institutions=institutions,
        credits_software=software
    )

    return render(request, 'website/index.html', context)
