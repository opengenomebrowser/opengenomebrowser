"""
Django settings for OpenGenomeBrowser project.
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = ''
assert SECRET_KEY != '', 'Change the security key in OpenGenomeBrowser/settings.py to a random string!'

CSRF_COOKIE_SECURE = True

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = False

ALLOWED_HOSTS = []

# Application definition

INSTALLED_APPS = [
    'dal',
    'dal_select2',
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'website.apps.WebsiteConfig',
    'rest_framework',
    'prettyjson',
    'huey.contrib.djhuey',
    'mptt'
]

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
        'ENGINE': 'django.db.backends.postgresql_psycopg2',
        'NAME': 'open_genome_browser_db',
        'USER': 'ogb_admin',
        'PASSWORD': '?????????????????????',
        'HOST': 'localhost',
        'PORT': '',
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
AUTH_EXEMPT_ROUTES = ('login', 'index')
AUTH_LOGIN_ROUTE = 'login'

# Huey config
HUEY = {
    'huey_class': 'huey.SqliteHuey',  # Huey implementation to use.
    'results': True,  # Store return values of tasks.
    'store_none': False,  # If a task returns None, do not save to results.
    'immediate': False,  # If DEBUG=True, run synchronously.
    'utc': True,  # Use UTC for all times internally.
    'consumer': {
        'workers': 4,
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

# Email settings
EMAIL_HOST = 'smtp.unibe.ch'
EMAIL_HOST_USER = 'noreply@bioinformatics.unibe.ch'
DEFAULT_FROM_EMAIL = 'noreply@bioinformatics.unibe.ch'
EMAIL_PORT = '25'

LOGIN_MESSAGE = 'Welcome to the OpenGenomeBrowser!'

ORTHOLOG_ANNOTATIONS = dict(
    # file that links ortholog identifiers with genes
    ortholog_to_gene_ids='/path/to/file.tsv',
    # links ortholog identifiers with descriptions
    ortholog_to_name=F'/path/to/file.tsv'
)

# where KEGG data should be loaded to (using import_database.py --download-kegg-data)
ANNOTATION_DATA = F'/path/to/database/annotations-data'

# GENOMIC_DATABASE must contain the folder 'organisms'
GENOMIC_DATABASE = F'/path/to/database'

# path (relative to GENOMIC_DATABASE) to pathway_maps-svgs
PATHWAY_MAPS_RELATIVE = 'pathway_maps/svgs'
# path (relative to GENOMIC_DATABASE) to type_dictionary.json
PATHWAY_MAPS_TYPE_DICT_RELATIVE = 'pathway_maps/type_dictionary.json'

# absolute path to OrthoFinder fasta folder
ORTHOFINDER_FASTAS = F'/path/to/OrthoFinder/fastas'
# file endings of the files in ORTHOFINDER_FASTAS. usually 'fasta' or 'faa'
ORTHOFINDER_FASTA_ENDINGS = 'faa'
# Name of the most recent 'Results'-folder, i.e. 'Results_Aug14'
ORTHOFINDER_LATEST_RUN = 'Results_Xxx00'

# genomes table: default columns
DEFAULT_GENOMES_COLUMNS = ["organism.name", "identifier", "organism.taxid.taxscientificname", "sequencing_tech"]
DEFAULT_GENOMES_PAGE_LENGTH = 'All'

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