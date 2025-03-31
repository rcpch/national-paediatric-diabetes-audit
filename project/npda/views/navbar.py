''' Contains views for navbar processing i.e. generation of a breadcrumb element'''

from django.http import HttpResponse
from django.urls import resolve
from django.urls import Resolver404
from django.template.loader import render_to_string

from project.constants.navbar_headers import NAVBAR_HEADERS

def generate_breadcrumbs(request):
    base_urls = [
        "https://npda-staging.rcpch.tech/",
        "https://npda.localhost/",
        "https://npda.rcpch.ac.uk/"
    ]
    current_url = request.META.get('HTTP_REFERER')

    for base_url in base_urls:
        if current_url.startswith(base_url):
            current_url = current_url.replace(base_url, "")


    print(f"Here is my tidied current_url with the local host removed: {current_url}")


    current_url = current_url.strip("/")
    segments = current_url.split("/")
    breadcrumbs = []
    current_url = ""
    for segment in segments:
        current_url += f"/{segment}"

        try:
            # Tries to find exact match in constants, so a url of /patients will map to 'Patient Data' on the breadcrumb
            match = resolve(current_url)
            name = NAVBAR_HEADERS[match.url_name] if match.url_name in NAVBAR_HEADERS else match.url_name.replace("_", " ").replace("-", " ").title()
        except Resolver404:
            # Exception case for uids or other urls not explicitly defined in constants NAVBAR_HEADERS
            name = segment.replace("_", " ").replace("-", " ").title()

        breadcrumbs.append({"name": name, "url": current_url})
    
    print(f"{segments}")
    print(f"previous url: {current_url}")
    print("Breadcrumbs context:", {"breadcrumbs": breadcrumbs})

    breadcrumb_html = render_to_string("navbar/components/breadcrumbs.html", {"breadcrumbs": breadcrumbs}, request=request)

    print("Generated HTML:", breadcrumb_html)

    return HttpResponse(breadcrumb_html)