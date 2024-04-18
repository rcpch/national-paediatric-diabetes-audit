from django.shortcuts import render
from django.views.generic.edit import CreateView, UpdateView, DeleteView
from django.urls import reverse_lazy
from django.contrib.messages.views import SuccessMessageMixin
from ..models import NPDAUser
from ..forms.npda_user_form import NPDAUserForm


def npda_users(request):
    """
    Return a list of all children
    """
    template_name = "npda_users.html"
    npda_users = NPDAUser.objects.all()
    context = {"npda_users": npda_users}
    return render(request=request, template_name=template_name, context=context)


class NPDAUserCreateView(SuccessMessageMixin, CreateView):
    """
    Handle creation of new patient in audit
    """

    model = NPDAUser
    form_class = NPDAUserForm
    success_message = "New NPDA user created was created successfully"
    success_url=reverse_lazy('npda_users')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Add New NPDA User"
        context["button_title"] = "Add NPDA User"
        context["form_method"] = "create"
        return context


class NPDAUserUpdateView(SuccessMessageMixin, UpdateView):
    """
    Handle update of patient in audit
    """

    model = NPDAUser
    form_class = NPDAUserForm
    success_message = "NPDA User record updated successfully"
    success_url=reverse_lazy('npda_users')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["title"] = "Edit NPDA User Details"
        context["button_title"] = "Edit NPDA User Details"
        context["form_method"] = "update"
        context["npda_user_id"] = self.kwargs['pk']
        return context
    
    def is_valid(self):
        return super(NPDAUserForm, self).is_valid()



class NPDAUserDeleteView(SuccessMessageMixin, DeleteView):
    """
    Handle deletion of child from audit
    """

    model = NPDAUser
    success_message = "NPDA User removed from database"
    success_url=reverse_lazy('npda_users')
