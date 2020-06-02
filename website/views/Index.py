from django.shortcuts import render, HttpResponse

from website.models.KeggMap import KeggMap


def index_view(request):
    personen = [
        dict(
            name='Thomas Roder',
            img='https://www.bioinformatics.unibe.ch/e132733/e132747/e649912/e698523/2020_01_14_12_44_31.jpg',
            img_cls='ibu',
            role='PhD student',
            href='https://www.bioinformatics.unibe.ch/about_us/team/index_eng.html#person698529',
            did=['Code', 'Concept']
        ),
        dict(
            name='Simone Oberhänsli',
            img='https://www.bioinformatics.unibe.ch/e132733/e132747/e649912/e649912/2020_01_14_12_45_48.jpg',
            img_cls='ibu',
            role='Staff scientist',
            href='https://www.bioinformatics.unibe.ch/about_us/team/index_eng.html#person649918',
            did=['Support', 'Ideas', 'Test data']
        ),
        dict(
            name='Rémy Bruggmann',
            img='https://www.bioinformatics.unibe.ch/e132733/e132747/e649912/e132748/2019_12_17_15_45_07.jpg',
            img_cls='ibu',
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
            img='https://www.grstiftung.ch/dam/jcr:77e5bf43-9924-46d8-b5a5-ca900745d025/Logo%20Twitter.jpg',
            img_cls='circle',
            role='Grant-ID: GRS-070/17',
            href='https://www.grstiftung.ch/',
            did=['Funding']
        ),
        dict(
            name='Interfaculty Bioinformatics Unit',
            img='https://www.unibe.ch/media/logo_unibern@2x.png',
            img_cls='square-offset-top',
            role='University of Bern',
            href='https://www.bioinformatics.unibe.ch/',
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
            img='https://upload.wikimedia.org/wikipedia/en/8/80/KEGG_database_logo.gif',
            img_cls='square-offset-top',
            role='KEGG',
            href='https://www.kegg.jp/',
            did=['Pathway maps']
        ),
        dict(
            name='National Center for Biotechnology Information',
            img='https://upload.wikimedia.org/wikipedia/commons/thumb/0/07/US-NLM-NCBI-Logo.svg/1200px-US-NLM-NCBI-Logo.svg.png',
            img_cls='ncbi',
            role='NCBI',
            href='https://blast.ncbi.nlm.nih.gov/Blast.cgi/',
            did=['BLAST alignment search', 'Taxonomy']
        ),
        dict(
            name='Blasterjs',
            img='http://www.sing-group.org/blasterjs/img/profile.png',
            img_cls='circle',
            role='SING Group, University of Vigo',
            href='http://www.sing-group.org/blasterjs/',
            did=['Visualize BLAST results']
        ),
        dict(
            name='DNA Features Viewer',
            img='https://edinburgh-genome-foundry.github.io/static/imgs/logos/dfv.png',
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
            img='https://upload.wikimedia.org/wikipedia/commons/thumb/7/7d/Biopython_logo.svg/1599px-Biopython_logo.svg.png',
            img_cls='square-offset-top',
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
