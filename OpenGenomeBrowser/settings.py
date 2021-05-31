"""
Django settings for OpenGenomeBrowser project.
"""

import os

# Build paths inside the project like this: os.path.join(BASE_DIR, ...)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Quick-start development settings - unsuitable for production
# See https://docs.djangoproject.com/en/dev/howto/deployment/checklist/

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = str(os.environ.get('DEBUG')).lower() == 'true'
CSRF_COOKIE_SECURE = not DEBUG

# SECURITY WARNING: keep the secret key used in production secret!
if 'DJANGO_SECRET_KEY' in os.environ:
    SECRET_KEY = os.environ.get('DJANGO_SECRET_KEY')
else:
    print('GENERATING RANDOM SECRET KEY')
    from django.core.management.utils import get_random_secret_key

    SECRET_KEY = get_random_secret_key()

ALLOWED_HOSTS = os.environ.get('DJANGO_ALLOWED_HOSTS').split(',')

# database
DB_HOST = os.environ.get('DB_HOST', 'db')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'opengenomebrowser_db')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'postgres')

# GENOMIC_DATABASE must contain the folder 'organisms'
GENOMIC_DATABASE = os.environ.get('GENOMIC_DATABASE', '/database')

CACHE_DIR = os.environ.get('CACHE_DIR', '/tmp/ogb-cache')
CACHE_MAXSIZE = int(os.environ.get('CACHE_MAXSIZE', 20))

ORTHOFINDER_ENABLED = os.environ.get('ORTHOFINDER_ENABLED', 'false').lower() == 'true'

PROTEIN_FASTA_ENDINGS = os.environ.get('PROTEIN_FASTA_ENDINGS')

# genomes table: default columns
if 'DEFAULT_COLUMNS' in os.environ:
    DEFAULT_GENOMES_COLUMNS = os.environ.get('DEFAULT_COLUMNS').split(',')
else:
    DEFAULT_GENOMES_COLUMNS = ["organism.name", "identifier", "organism.taxid.taxscientificname", "sequencing_tech"]

DEFAULT_GENOMES_PAGE_LENGTH = os.environ.get('DEFAULT_GENOMES_PAGE_LENGTH', 'All')

# Email settings
if all([var in os.environ for var in ['EMAIL_HOST', 'EMAIL_HOST_USER', 'DEFAULT_FROM_EMAIL', 'EMAIL_PORT']]):
    EMAIL_HOST = os.environ.get('EMAIL_HOST')
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    DEFAULT_FROM_EMAIL = os.environ.get('DEFAULT_FROM_EMAIL')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT'))

LOGIN_MESSAGE = os.environ.get('LOGIN_MESSAGE', 'Welcome to OpenGenomeBrowser!')

DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

HUEY_WORKERS = int(os.environ.get('HUEY_WORKERS', 4))

# Application definition
INSTALLED_APPS = [
    # 'django.contrib.admin',
    'OpenGenomeBrowser.apps.OgbAdminConfig',
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
    'django.middleware.clickjacking.XFrameOptionsMiddleware'
]
if os.environ.get('LOGIN_REQUIRED', 'true') == 'true':
    # require login unless LOGIN_REQUIRED is set to 'false'
    MIDDLEWARE.append('OpenGenomeBrowser.login_required_middleware.LoginRequiredMiddleware')
else:
    print('NO LOGIN REQUIRED TO ACCESS THIS INSTANCE OF OPENGENOMEBROWSER!')

REST_FRAMEWORK = {
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 50
}

ROOT_URLCONF = 'OpenGenomeBrowser.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        # 'DIRS': [os.path.join(BASE_DIR, 'templates')]
        'DIRS': [os.path.join(BASE_DIR, 'website', 'templates')],
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
        'NAME': DB_NAME,
        'USER': DB_USER,
        'PASSWORD': DB_PASSWORD,
        'HOST': DB_HOST,
        'PORT': DB_PORT,
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

ORTHOLOG_ANNOTATIONS = f'{GENOMIC_DATABASE}/orthologs/orthologs.tsv'

# where KEGG data should be loaded to (using manage_ogb.py --download-kegg-data)
ANNOTATION_DESCRIPTIONS = f'{GENOMIC_DATABASE}/annotation-descriptions'

# path (relative to GENOMIC_DATABASE) to pathway_maps-svgs
PATHWAY_MAPS_RELATIVE = 'pathway_maps/svg'
# path (relative to GENOMIC_DATABASE) to type_dictionary.json
PATHWAY_MAPS_TYPE_DICT_RELATIVE = 'pathway_maps/type_dictionary.json'

# Path to the folder that contains the orthofinder binary
ORTHOFINDER_INSTALL_DIR = '/opt/OrthoFinder_source'
# absolute path to OrthoFinder fasta folder
ORTHOFINDER_FASTAS = f'{GENOMIC_DATABASE}/OrthoFinder/fastas'

#
#
# sanity checks, do not edit what is below here.
#
#
PATHWAY_MAPS_TYPE_DICT = f'{GENOMIC_DATABASE}/{PATHWAY_MAPS_TYPE_DICT_RELATIVE}'
PATHWAY_MAPS = f'{GENOMIC_DATABASE}/{PATHWAY_MAPS_RELATIVE}'

# Name of the most recent 'Results'-folder, i.e. 'Results_Aug14'
if ORTHOFINDER_ENABLED:
    ORTHOFINDER_LATEST_RUN = max(
        [os.path.join(f'{ORTHOFINDER_FASTAS}/OrthoFinder', d) for d in os.listdir(f'{ORTHOFINDER_FASTAS}/OrthoFinder')],
        key=os.path.getmtime
    )

    for folder in [ORTHOFINDER_FASTAS, ORTHOFINDER_LATEST_RUN]:
        assert os.path.isdir(folder), F"The path in settings.py doesn't point to a folder: {folder}"

    for file in [ORTHOLOG_ANNOTATIONS]:
        assert os.path.isfile(file), F"The path in settings.py doesn't point to a file: {file}"


else:
    ORTHOFINDER_LATEST_RUN = None

for folder in [PATHWAY_MAPS, GENOMIC_DATABASE]:
    assert os.path.isdir(folder), F"The path in settings.py doesn't point to a folder: {folder}"

for file in [PATHWAY_MAPS_TYPE_DICT]:
    assert os.path.isfile(file), F"The path in settings.py doesn't point to a file: {file}"

if DEFAULT_GENOMES_PAGE_LENGTH.isnumeric():
    DEFAULT_GENOMES_PAGE_LENGTH = int(DEFAULT_GENOMES_PAGE_LENGTH)
assert DEFAULT_GENOMES_PAGE_LENGTH in ["All", 10, 25, 50, 100, 200, 400, 800, 1600]
