from django.http import HttpResponseServerError
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path


def response_error_handler(request, exception=None):
    return HttpResponse("Error handler content", status=500)


def internal_error_view(request):
    return HttpResponseServerError(content="Error handler content")


urlpatterns = [
    path("500/", internal_error_view),
]

handler500 = response_error_handler


@override_settings(ROOT_URLCONF=__name__)
class CustomErrorHandlerTests(SimpleTestCase):
    def test_handler_renders_template_response(self):
        response = self.client.get("/500/")
        # Make assertions on the response here. For example:
        self.assertEqual(response.status_code,500)
        self.assertTemplateUsed(response,'errors/500.html')