from django.shortcuts import render

from django.http import HttpResponseServerError

def error_400(request, exception):
        context = {}
        return render(request=request,template_name='errors/400.html', context=context)

def error_403(request, exception):
        context = {}
        return render(request=request,template_name='errors/403.html', context=context)

def error_404(request, exception):
        context = {}
        return render(request=request, template_name='errors/404.html', context=context)

def error_500(request):
        context = {}
        return render(request=request,template_name='errors/500.html', context=context)

def csrf_fail(request):
        context = {}
        return render(request=request,template_name='errors/csrf_fail.html', context=context)