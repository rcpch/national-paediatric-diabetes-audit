from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from ..models import Patient


class PatientCreateView(CreateView):
    model = Patient
    fields = ["nhs_number",
            "sex",
            "date_of_birth",
            "postcode",
            "ethnicity",
            "diabetes_type",
            "diagnosis_date",
            "death_date",
            "gp_practice_ods_code",
            "gp_practice_postcode"]


class PatientUpdateView(UpdateView):
    model = Patient
    fields = ["nhs_number",
            "sex",
            "date_of_birth",
            "postcode",
            "ethnicity",
            "diabetes_type",
            "diagnosis_date",
            "death_date",
            "gp_practice_ods_code",
            "gp_practice_postcode"]


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