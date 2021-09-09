from django.contrib import messages
from django.http import HttpResponseRedirect


def download_taxdump(request):
    try:
        from lib.get_tax_info.get_tax_info import GetTaxInfo
        GetTaxInfo().update_ncbi_taxonomy_from_web()
        messages.add_message(request, messages.SUCCESS, f'Downloaded the latest NCBI taxdump!')
    except Exception as e:
        messages.add_message(request, messages.ERROR, f'Something went wrong: {str(e)}')
    return HttpResponseRedirect('/admin/website/taxid/')


def reload_taxids(request):
    from db_setup.manage_ogb import update_taxids
    try:
        update_taxids(download_taxdump=False)
        messages.add_message(request, messages.SUCCESS, f'Reloaded the taxids!')
    except Exception as e:
        messages.add_message(request, messages.ERROR, f'Something went wrong: {str(e)}')
    return HttpResponseRedirect('/admin/website/taxid/')


def reload_css(request):
    from db_setup.manage_ogb import reload_color_css
    try:
        reload_color_css()
        messages.add_message(request, messages.SUCCESS, f'Reloaded the css files, use Ctrl+F5 to reload them!')
    except Exception as e:
        messages.add_message(request, messages.ERROR, f'Something went wrong: {str(e)}')
    return HttpResponseRedirect('/admin/')


def delete_sunburst_cache(request):
    import os, shutil
    from OpenGenomeBrowser.settings import CACHE_DIR
    sunburst_cache_dir = f'{CACHE_DIR}/website.views.Home.sunburst'
    if os.path.isdir(sunburst_cache_dir):
        shutil.rmtree(sunburst_cache_dir)
        messages.add_message(request, messages.SUCCESS, f'Deleted sunburst cache!')
    else:
        messages.add_message(request, messages.ERROR, f'No cache found.')
    return HttpResponseRedirect('/admin/')
