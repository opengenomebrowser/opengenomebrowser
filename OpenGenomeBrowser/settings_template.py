"""
Django settings for OpenGenomeBrowser project.
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS').split(',')

PROTEIN_FASTA_ENDINGS = os.environ.get('PROTEIN_FASTA_ENDINGS')

ORTHOFINDER_LATEST_RUN = os.environ.get('ORTHOFINDER_LATEST_RUN')

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG').lower() == 'true'
assert type(DEBUG) is bool
CSRF_COOKIE_SECURE = not DEBUG

# genomes table: default columns
if 'DEFAULT_COLUMNS' in os.environ:
    DEFAULT_GENOMES_COLUMNS = [os.environ.get('DEFAULT_COLUMNS').split(',')]
else:
    DEFAULT_GENOMES_COLUMNS = ["organism.name", "identifier", "organism.taxid.taxscientificname", "sequencing_tech"]

DEFAULT_GENOMES_PAGE_LENGTH = os.environ.get('DEFAULT_GENOMES_PAGE_LENGTH', 'All')

# Email settings
if all([var in os.environ for var in ['EMAIL_HOST', 'EMAIL_HOST_USER', 'DEFAULT_FROM_EMAIL', 'EMAIL_PORT']]):
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT'))
    # print(f'MAIL SETTINGS:\n'
    #       f'{EMAIL_HOST=}\n{EMAIL_HOST_USER=}\n{DEFAULT_FROM_EMAIL=}\n{EMAIL_PORT=}')

LOGIN_MESSAGE = os.environ.get('LOGIN_MESSAGE', 'Welcome to OpenGenomeBrowser!')

HUEY_WORKERS = int(os.environ.get('HUEY_WORKERS', 4))

# print(f'SETTINGS:\n'
#       f'{SECRET_KEY=}\n{ALLOWED_HOSTS=}\n{PROTEIN_FASTA_ENDINGS=}\n{ORTHOFINDER_LATEST_RUN=}\n{DEBUG=}\n{CSRF_COOKIE_SECURE=}\n'
#       f'{DEFAULT_GENOMES_COLUMNS=}\n{DEFAULT_GENOMES_PAGE_LENGTH=}\n{LOGIN_MESSAGE=}\n{HUEY_WORKERS=}')

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    # easy api
    'rest_framework',
    # edit json in admin view
    'prettyjson',
    # job scheduler
    'huey.contrib.djhuey',
    # hierarchical data structures for database (used in TaxID)
    'mptt',
    'website.apps.WebsiteConfig'
]

# SITE_ID = 1  # required because of 'invitations'

MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'OpenGenomeBrowser.login_required_middleware.LoginRequiredMiddleware',
]

ROOT_URLCONF = 'OpenGenomeBrowser.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [os.path.join(BASE_DIR, 'templates')]
        ,
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'OpenGenomeBrowser.wsgi.application'

DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': 'opengenomebrowser_db',
        'USER': 'postgres',
        'PASSWORD': 'postgres',
        'HOST': 'db',
        'PORT': '5432',
    }
}

# Password validation
# https://docs.djangoproject.com/en/2.2/ref/settings/#auth-password-validators

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
# https://docs.djangoproject.com/en/2.2/topics/i18n/

LANGUAGE_CODE = 'en-us'

TIME_ZONE = 'UTC'

USE_I18N = True

USE_L10N = True

USE_TZ = True

# Static files (CSS, JavaScript, Images)
# https://docs.djangoproject.com/en/2.2/howto/static-files/

STATIC_URL = '/static/'
STATIC_ROOT = 'static_root/'

# Media files (created and removed by Django)
# https://pypi.org/project/django-remote-submission/
MEDIA_URL = '/media/'
MEDIA_ROOT = 'dist/media'

# Require login by default, see also OpenGenomeBrowser.login_required_middleware.LoginRequiredMiddleware
# https://stackoverflow.com/questions/3214589/django-how-can-i-apply-the-login-required-decorator-to-my-entire-site-excludin/56579091#56579091
AUTH_EXEMPT_ROUTES = ('login', 'index', 'logout', 'password_change', 'password_change_done', 'password_reset')
AUTH_LOGIN_ROUTE = 'login'

# Huey config
HUEY = {
    'huey_class': 'huey.SqliteHuey',  # Huey implementation to use.
    'results': True,  # Store return values of tasks.
    'store_none': False,  # If a task returns None, do not save to results.
    'immediate': False,  # If DEBUG=True, run synchronously.
    'utc': True,  # Use UTC for all times internally.
    'consumer': {
        'workers': HUEY_WORKERS,
        'worker_type': 'thread',
        'initial_delay': 0.1,  # Smallest polling interval, same as -d.
        'backoff': 1.15,  # Exponential backoff using this rate, -b.
        'max_delay': 10.0,  # Max possible polling interval, -m.
        'scheduler_interval': 1,  # Check schedule every second, -s.
        'periodic': True,  # Enable crontab feature.
        'check_worker_health': True,  # Enable worker health checks.
        'health_check_interval': 10,  # Check worker health every second.
    },
}

ORTHOLOG_ANNOTATIONS = dict(
    # file that links ortholog identifiers with genes
    ortholog_to_gene_ids=F'/database/global_annotations/HOG_gene_ids.tsv',
    # ortholog_to_gene_ids=F'{BASE_DIR}/database/global_annotations/mock_ids.tsv',
    # links ortholog identifiers with descriptions
    ortholog_to_name=F'/database/global_annotations/HOG_best_name.tsv'
)

# GENOMIC_DATABASE must contain the folder 'organisms'
GENOMIC_DATABASE = F'/database'

# where KEGG data should be loaded to (using import_database.py --download-kegg-data)
ANNOTATION_DATA = F'/database/global_annotations'

# path (relative to GENOMIC_DATABASE) to pathway_maps-svgs
PATHWAY_MAPS_RELATIVE = 'pathway_maps/svg'
# path (relative to GENOMIC_DATABASE) to type_dictionary.json
PATHWAY_MAPS_TYPE_DICT_RELATIVE = 'pathway_maps/type_dictionary.json'

# Path to the folder that contains the orthofinder binary
ORTHOFINDER_INSTALL_DIR = '/opt/OrthoFinder'
# absolute path to OrthoFinder fasta folder
ORTHOFINDER_FASTAS = F'/database/OrthoFinder/fastas'

#
#
# sanity checks, do not edit what is below here.
#
#
PATHWAY_MAPS_TYPE_DICT = F'{GENOMIC_DATABASE}/{PATHWAY_MAPS_TYPE_DICT_RELATIVE}'
PATHWAY_MAPS = os.path.join(GENOMIC_DATABASE, PATHWAY_MAPS_RELATIVE)  # do not change this line!

ORTHOFINDER_LATEST_RUN = F'{ORTHOFINDER_FASTAS}/OrthoFinder/{ORTHOFINDER_LATEST_RUN}'

for folder in [ORTHOFINDER_FASTAS, ORTHOFINDER_LATEST_RUN, PATHWAY_MAPS, GENOMIC_DATABASE]:
    assert os.path.isdir(folder), F"The path in settings.py doesn't point to a folder: {folder}"

for file in ['ortholog_to_gene_ids', 'ortholog_to_name']:
    assert file in ORTHOLOG_ANNOTATIONS, F"ORTHOLOG_ANNOTATIONS does not contain {file}"
    assert os.path.isfile(ORTHOLOG_ANNOTATIONS[file]), F"The path in settings.py doesn't point to a file: {file}"

for file in [PATHWAY_MAPS_TYPE_DICT]:
    assert os.path.isfile(file), F"The path in settings.py doesn't point to a file: {file}"

assert DEFAULT_GENOMES_PAGE_LENGTH in ["All", 10, 25, 50, 100, 200, 400, 800, 1600]
