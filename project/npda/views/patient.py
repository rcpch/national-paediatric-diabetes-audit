from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from ..models import Patient
from ..forms.patient_form import PatientForm


def patients(request):
    """
    Return a list of all children
    """
    template_name = "patients.html"
    patients = Patient.objects.all()
    context = {"patients": patients}
    return render(request=request, template_name=template_name, context=context)


class PatientCreateView(CreateView):
    """
    Handle creation of new patient in audit
    """

    model = Patient
    form_class = PatientForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add New Child"
        context["button_title"] = "Add New Child"
        return context


class PatientUpdateView(UpdateView):
    """
    Handle update of patient in audit
    """

    model = Patient
    form_class = PatientForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Child Details"
        context["button_title"] = "Edit Child Details"
        return context


class PatientDeleteView(DeleteView):
    """
    Handle deletion of child from audit
    """

    model = Patient
    success_url = reverse_lazy("patients")
