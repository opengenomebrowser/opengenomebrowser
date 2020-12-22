from website.models import Organism
from django.views.generic import DetailView


class OrganismDetailView(DetailView):
    model = Organism
    slug_field = 'name'
    template_name = 'website/organism_detail.html'
    context_object_name = 'organism'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['no_help'] = True

        o: Organism = self.object

        context['title'] = o.name

        return context
