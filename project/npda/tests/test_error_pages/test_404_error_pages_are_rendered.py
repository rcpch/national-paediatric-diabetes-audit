from django.http import Http404
from django.http import HttpResponse
from django.test import SimpleTestCase, override_settings
from django.urls import path

urlpatterns = [
]
@override_settings(ROOT_URLCONF=__name__)
class CustomErrorHandlerTests(SimpleTestCase):
    def test_handler_renders_template_response(self):
        response = self.client.get("/nonExistentPageLink/")
        # Make assertions on the response here. For example:
        self.assertEqual(response.status_code,404)
        print(response)
        self.assertTemplateUsed(response,'errors/404.html')
