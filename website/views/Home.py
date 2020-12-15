from django.shortcuts import render


def home_view(request):
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
                did=['Infrastructure']
            ),
            dict(
                name='Agroscope',
                img='/static/index/images/agroscope.png',
                img_cls='square',
                role='Swiss center for agricultural research',
                href='https://www.agroscope.admin.ch/',
                did=['Infrastructure']
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
                name='GitHub',
                img='/static/index/images/GitHub.svg',
                img_cls='square',
                role='Code repository',
                href='https://opengenomebrowser.github.io/opengenomebrowser/',
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
    )

    context = dict(
        title='Home',
        credit=credit
    )

    return render(request, 'website/index.html', context)
