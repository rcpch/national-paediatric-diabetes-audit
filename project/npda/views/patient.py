from django.views.generic import DetailView
from ..models import Patient
from django.views.generic.edit import FormMixin
from ..forms.patientdetail import PatientForm


class PatientDetailView(FormMixin, DetailView):
    model = Patient
    template_name = "patient_detail.html"
    form_class = PatientForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = PatientForm(initial={"post": self.object})
        context["hx_trigger_id"] = "update-form"
        return context
