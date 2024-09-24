from django.core.exceptions import SuspiciousOperation
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path


# def response_error_handler(request, exception=None):
#     return HttpResponse("Error handler content", status=400)


def bad_request_view(request):
    raise SuspiciousOperation


urlpatterns = [
    path("400/", bad_request_view),
]

# handler400 = response_error_handler


@override_settings(ROOT_URLCONF=__name__)
class CustomErrorHandlerTests(SimpleTestCase):
    def test_handler_renders_template_response(self):
        response = self.client.get("/400/", follow=True)
        # Make assertions on the response here. For example:
        self.assertEqual(response.status_code,400)
        self.assertTemplateUsed(response,'errors/400.html')