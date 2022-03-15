from website.models import Tag
from django.views.generic import DetailView


class TagDetailView(DetailView):
    model = Tag
    slug_field = 'tag'
    template_name = 'website/tag_detail.html'
    context_object_name = 'tag'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['no_help'] = True

        t: Tag = self.object

        context['title'] = t.tag

        context['admin_actions'] = [
            dict(url=f'/admin/website/tag/{t.tag}/change/', action='Edit tag'),
        ]

        return context
