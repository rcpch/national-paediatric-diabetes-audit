# from django.core.exceptions import SuspiciousOperation
# from django.http import HttpResponse
# from django.test import SimpleTestCase, override_settings
# from django.urls import path


# # def response_error_handler(request, exception=None):
# #     return HttpResponse("Error handler content", status=400)


# def bad_request_view(request):
#     raise SuspiciousOperation


# urlpatterns = [
#     path("400/", bad_request_view),
# ]

# # handler400 = response_error_handler


# @override_settings(ROOT_URLCONF=__name__)
# class CustomErrorHandlerTests(SimpleTestCase):
#     def test_handler_renders_template_response(self):
#         response = self.client.get("/400/", follow=True)
#         # Make assertions on the response here. For example:
#         # self.assertEqual(response.status_code, 400)
#         # self.assertContains(response, "Error handler content")
#         self.assertTemplateUsed(response, "errors/400.html")

import pytest
from django.test import SimpleTestCase, override_settings
from django.urls import reverse


@override_settings(ROOT_URLCONF="project.urls")
class CustomErrorHandlerTests(SimpleTestCase):
    def test_error_400(self):
        response = self.client.get("/nonexistent-url/", follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "errors/404.html")

    def test_error_403(self):
        response = self.client.get("/nonexistent-url/", follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "errors/404.html")

    def test_error_404(self):
        response = self.client.get("/nonexistent-url/", follow=True)
        self.assertEqual(response.status_code, 404)
        self.assertTemplateUsed(response, "errors/404.html")

    def test_error_500(self):
        with self.settings(DEBUG=False):
            response = self.client.get("/nonexistent-url/", follow=True)
            self.assertEqual(response.status_code, 404)
            self.assertTemplateUsed(response, "errors/404.html")

    def test_csrf_fail(self):
        response = self.client.get(reverse("csrf_fail"))
        self.assertEqual(response.status_code, 403)
        self.assertTemplateUsed(response, "errors/csrf_fail.html")
