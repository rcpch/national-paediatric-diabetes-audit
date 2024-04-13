from typing import Any
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from ..models import Patient
from ..forms.patient_form import PatientForm


class PatientCreateView(CreateView):
    model = Patient
    form_class = PatientForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add New Child"
        context["button_title"] = "Add New Child"
        return context


class PatientUpdateView(UpdateView):
    model = Patient
    form_class = PatientForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Child Details"
        context["button_title"] = "Edit Child Details"
        return context


class PatientDeleteView(DeleteView):
    model = Patient
    success_url = reverse_lazy("patients")


# class PatientFormView(FormView):
#     template_name = "patient_form.html"
#     form_class = PatientForm
#     success_url = "/thanks/"

#     def form_valid(self, form):
#         # This method is called when valid form data has been POSTed.
#         # It should return an HttpResponse.
#         print("form is valid")
#         return super().form_valid(form)
