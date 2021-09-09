from django.shortcuts import render
from django.core.files.uploadhandler import FileUploadHandler
from OpenGenomeBrowser.settings import CACHE_DIR, CACHE_MAXSIZE

from django import forms
from django.views.generic.edit import FormView


class GenomeUploadForm(forms.Form):
    file_field = forms.FileField(widget=forms.ClearableFileInput(attrs={'multiple': True}))


class GenomeUploadView(FormView):
    form_class = GenomeUploadForm
    template_name = 'admin/genome_upload.html'  # Replace with your template(which you created)
    success_url = 'admin/add-genome/success/'

    def post(self, request, *args, **kwargs):
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        files = request.FILES.getlist('file_field')
        if form.is_valid():
            for f in files:
                print(f)
            return self.form_valid(form)
        else:
            return self.form_invalid(form)
