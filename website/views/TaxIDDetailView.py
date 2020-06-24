from website.models import TaxID
from django.views.generic import DetailView
from django.shortcuts import redirect
from django.contrib.auth.mixins import LoginRequiredMixin


class TaxIDDetailView(LoginRequiredMixin, DetailView):
    model = TaxID
    slug_field = 'id'
    template_name = 'website/taxid_detail.html'
    context_object_name = 'taxid'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        t: TaxID = self.object

        context['title'] = t.taxscientificname

        return context

    @staticmethod
    def redirect_taxname(request, slug):

        t = TaxID.objects.get(taxscientificname=slug)

        return redirect(F'/taxid/{t.id}')
