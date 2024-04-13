from typing import Any
from django.views.generic.edit import CreateView, UpdateView, DeleteView, FormView
from django.urls import reverse_lazy
from ..models import Visit
from ..forms.visit_form import VisitForm


class VisitCreateView(CreateView):
    model = Visit
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add New Child"
        context["button_title"] = "Add New Child"
        return context


class VisitUpdateView(UpdateView):
    model = Visit
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit Child Details"
        context["button_title"] = "Edit Child Details"
        return context


class VisitDeleteView(DeleteView):
    model = Visit
    success_url = reverse_lazy("patient_visits")
