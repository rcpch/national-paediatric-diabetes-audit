from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
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


class PatientCreateView(SuccessMessageMixin, CreateView):
    """
    Handle creation of new patient in audit
    """

    model = Patient
    form_class = PatientForm
    success_message = "New child record created was created successfully"
    success_url=reverse_lazy('patients')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add New Child"
        context["button_title"] = "Add New Child"
        context["form_method"] = "create"
        return context


class PatientUpdateView(SuccessMessageMixin, UpdateView):
    """
    Handle update of patient in audit
    """

    model = Patient
    form_class = PatientForm
    success_message = "New child record updated successfully"
    success_url=reverse_lazy('patients')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Child Details"
        context["button_title"] = "Edit Child Details"
        context["form_method"] = "update"
        context["patient_id"] = self.kwargs['pk']
        return context


class PatientDeleteView(SuccessMessageMixin, DeleteView):
    """
    Handle deletion of child from audit
    """

    model = Patient
    success_message = "Child removed from database"
    success_url=reverse_lazy('patients')
