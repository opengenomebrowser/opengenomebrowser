from website.models import Strain
from django.views.generic import DetailView
from django.contrib.auth.mixins import LoginRequiredMixin


class StrainDetailView(LoginRequiredMixin, DetailView):
    model = Strain
    slug_field = 'name'
    template_name = 'website/strain_detail.html'
    context_object_name = 'strain'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        s: Strain = self.object

        context['title'] = s.name

        return context
