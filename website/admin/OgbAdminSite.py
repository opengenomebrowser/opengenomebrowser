from django.contrib import admin, messages
from django.urls import path
from django.shortcuts import render
from django.core.exceptions import ObjectDoesNotExist
from django.http import JsonResponse, HttpResponseRedirect

from website.admin.MarkdownObject import MarkdownObjectPage, MarkdownObjectOrganism, MarkdownObjectGenome


class OgbAdminSite(admin.AdminSite):
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path(r'download-taxdump/', self.admin_view(self.download_taxdump), name='download-taxdump'),
            path(r'reload-taxids/', self.admin_view(self.reload_taxids), name='reload-taxids'),
            path(r'markdown-editor/', self.admin_view(self.markdown_editor), name='markdown-editor'),
            path(r'markdown-editor/submit/', self.admin_view(self.markdown_submit), name='markdown-editor-submit')
        ]
        urls = custom_urls + urls
        return urls

    def download_taxdump(self, request):
        try:
            from lib.get_tax_info.get_tax_info import GetTaxInfo
            GetTaxInfo().update_ncbi_taxonomy_from_web()
            messages.add_message(request, messages.SUCCESS, f'Downloaded the latest NCBI taxdump!')
        except Exception as e:
            messages.add_message(request, messages.ERROR, f'Something went wrong: {str(e)}')
        return HttpResponseRedirect('/admin/website/taxid/')

    def reload_taxids(self, request):
        from db_setup.manage_ogb import update_taxids
        try:
            update_taxids(download_taxdump=False)
            messages.add_message(request, messages.SUCCESS, f'Reloaded the taxids!')
        except Exception as e:
            messages.add_message(request, messages.ERROR, f'Something went wrong: {str(e)}')
        return HttpResponseRedirect('/admin/website/taxid/')

    def markdown_editor(self, request):
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

    def markdown_submit(self, request):
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
