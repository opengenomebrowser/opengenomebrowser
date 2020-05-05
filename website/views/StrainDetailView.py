from website.models import Strain
from django.views.generic import DetailView


class StrainDetailView(DetailView):
    model = Strain
    slug_field = 'name'
    template_name = 'website/strain_detail.html'
    context_object_name = 'strain'
