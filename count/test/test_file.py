from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from count.models import File


class FileTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('celery_upload_file')
        cls.user = mommy.make(User)

    def setUp(self):
        self.client.force_login(self.user)

    def test_celery_upload_file_not_zip_unsuccessfully(self):
        data = {
            'file': 'Documents/FileProject_samples/sample1/sample3/file1.txt',
            'user': self.user,
        }

        response = self.client.post(self.url, data, formt='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # how check the message error is shown:
        # {"non_field_errors": ["Uploaded File Is Not Zipped!"]}

    def test_celery_upload_file_wrong_structure_unsuccessfully(self):
        data = {
            'file': 'Documents/FileProject_samples/sample2.zip',
            'user': self.user.id,
        }

        response = self.client.post(self.url, data, formt='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # how check the message error is shown:
        # {"non_field_errors": ["Invalid Items!"]}

    def test_celery_upload_file_exists_unsuccessfully(self):
        obj_path = 'Documents/uploaded_files/user_{0}/sample1.zip'.format(self.user.id)
        first_file_obj = File(
            file=obj_path,
            path=obj_path,
            display_name='sample8.zip',
            user=self.user,
            category=None
        )
        first_file_obj.save()

        data = {
            'file': 'Documents/FileProject_samples/sample8.zip',
            'user': self.user.id
        }

        response = self.client.post(self.url, data, formt='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # how check the message error is shown:
        # {"non_field_errors": ["Change The Zip File Name!"]}

    def test_celery_upload_file_successfully(self):
        data = {
            'file': 'Documents/FileProject_samples/sample1.zip',
            'user': self.user.id
        }

        response = self.client.post(self.url, data, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
