from django.views.generic import TemplateView


class _AboutView(TemplateView):
    template_name = "pages/about.html"


about = _AboutView.as_view()
