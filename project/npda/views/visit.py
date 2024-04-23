from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.urls import reverse_lazy,reverse
from django.http import HttpResponseRedirect
from ..models import Visit, Patient
from ..forms.visit_form import VisitForm
from ..general_functions import get_visit_categories


def patient_visits(request, patient_id):
    """
    returns a list of visits and visit data
    """
    template_name = "visits.html"
    patient = Patient.objects.get(pk=patient_id)
    visits = Visit.objects.filter(patient=patient)
    calculated_visits = []
    for visit in visits:
        visit_categories = get_visit_categories(visit)
        calculated_visits.append({"visit": visit, "categories": visit_categories})
    context = {"visits": calculated_visits, "patient": patient}
    return render(request=request, template_name=template_name, context=context)


class VisitCreateView(SuccessMessageMixin, CreateView):
    model = Visit
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient_id"] = self.kwargs["patient_id"]
        context["title"] = "Add New Visit"
        context["form_method"] = "create"
        context["button_title"] = "Add New Visit"
        return context
    
    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "New visit added successfully")
        return reverse('patient_visits', kwargs={'patient_id': self.kwargs['patient_id']})
    
    def get_initial(self):
        initial =  super().get_initial()
        patient = Patient.objects.get(pk=self.kwargs['patient_id'])
        initial['patient']=patient
        return initial
    
    def form_valid(self, form, **kwargs):
        self.object = form.save(commit=False)
        self.object.patient_id = self.kwargs['patient_id']
        super(VisitCreateView, self).form_valid(form)
        return HttpResponseRedirect(self.get_success_url())


class VisitUpdateView(UpdateView):
    model = Visit
    form_class = VisitForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["patient_id"] = self.kwargs["patient_id"]
        context["title"] = "Edit Visit Details"
        context["button_title"] = "Edit Visit Details"
        context["form_method"] = "update"
        return context
    
    def get_success_url(self):
        messages.add_message(self.request, messages.SUCCESS, "Visit edited successfully")
        return reverse('patient_visits', kwargs={'patient_id': self.kwargs['patient_id']})
    
    def get_initial(self):
        initial =  super().get_initial()
        patient = Patient.objects.get(pk=self.kwargs['patient_id'])
        initial['patient']=patient
        return initial


class VisitDeleteView(SuccessMessageMixin, DeleteView):
    model = Visit
    success_url = reverse_lazy("patient_visits")
    success_message = "Visit removed successfully"