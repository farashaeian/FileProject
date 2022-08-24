from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User


class FileTests(APITestCase):
    def setUp(self):
        self.url = reverse('celery_upload_file')

    def test_celery_upload_file_successfully(self):
        pass
