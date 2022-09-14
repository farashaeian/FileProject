from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from count.models import File, Category
from zipfile import ZipFile
import os
from count.tasks import unzip


class UploadFileTestsUnsuccessfully(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('celery_upload_file')
        cls.user = mommy.make(User)

    def setUp(self):
        self.client.force_login(self.user)

    def test_celery_upload_file_not_zip_unsuccessfully(self):
        file_from_system = "count/test/sample_zip_files/sampleproject1.txt"

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # check the {"non_field_errors": ["Uploaded File Is Not Zipped!"]} :
        self.assertEqual(response.data['non_field_errors'][0], "Uploaded File Is Not Zipped!")

    def test_celery_upload_file_wrong_structure_unsuccessfully(self):
        file_from_system = "count/test/sample_zip_files/sample2.zip"

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # check the message {"non_field_errors": ["Invalid Items!"]} :
        self.assertEqual(response.data['non_field_errors'], ["Invalid Items!"])

    def test_celery_upload_file_exists_unsuccessfully(self):
        file_from_system = "count/test/sample_zip_files/sample8.zip"
        zipfile_name = ZipFile(file_from_system).filename
        obj_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, zipfile_name)
        first_file_obj = File(
            file=file_from_system,
            path=obj_path,
            display_name='sample8.zip',
            user=self.user,
            category=None
        )
        first_file_obj.save()

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # check the message {"non_field_errors": ["Change The Zip File Name!"]} :
        self.assertEqual(response.data['non_field_errors'], ["Change The Zip File Name!"])
