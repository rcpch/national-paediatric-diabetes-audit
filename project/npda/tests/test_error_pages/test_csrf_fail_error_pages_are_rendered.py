from django.http import HttpResponseForbidden
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path


def response_error_handler(request, exception=None):
    return HttpResponse("Error handler content", status=200)


def csrf_failed_view(request):
    return HttpResponseForbidden(content="Error handler content")


urlpatterns = [
    path("500/", csrf_failed_view),
]

CSRF_FAILURE_VIEW = response_error_handler


@override_settings(ROOT_URLCONF=__name__)
class CustomErrorHandlerTests(SimpleTestCase):
    def test_handler_renders_template_response(self):
        response = self.client.get("/500/")

        # Make assertions on the response here. For example:
        self.assertEqual(response.status_code,403)
        self.assertTemplateUsed(response,'errors/csrf_fail.html')