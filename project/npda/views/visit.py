from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from ..models import Visit, Patient
from ..forms.visit_form import VisitForm


def patient_visits(request, patient_id):
    """
    returns a list of visits and visit data
    """
    template_name = "visits.html"
    patient = Patient.objects.get(pk=patient_id)
    visits = Visit.objects.filter(patient=patient)
    context = {"visits": visits, "patient": patient}
    return render(request=request, template_name=template_name, context=context)


class VisitCreateView(CreateView):
    model = Visit
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add New Visit"
        context["button_title"] = "Add New Visit"
        return context


class VisitUpdateView(UpdateView):
    model = Visit
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Visit Details"
        context["button_title"] = "Edit Visit Details"
        return context


class VisitDeleteView(DeleteView):
    model = Visit
    success_url = reverse_lazy("patient_visits")
