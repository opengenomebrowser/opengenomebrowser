from website.models import TaxID
from django.views.generic import DetailView


class TaxIDDetailView(DetailView):
    model = TaxID
    slug_field = 'id'
    template_name = 'website/taxid_detail.html'
    context_object_name = 'taxid'
