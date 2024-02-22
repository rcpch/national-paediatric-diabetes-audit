from django.shortcuts import get_object_or_404, redirect, render


def home(request):
    context = {}
    template = "home.html"
    print("home")
    return render(request=request, template_name=template, context=context)
