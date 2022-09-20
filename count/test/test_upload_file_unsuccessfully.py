from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from count.models import File, Category
from zipfile import ZipFile
from django_celery_results.models import TaskResult


class UploadFileTestsUnsuccessfully(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('celery_upload_file')
        cls.user = mommy.make(User)

    def setUp(self):
        self.client.force_login(self.user, id=4)

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

    def test_celery_upload_file_exists_with_success_status_unsuccessfully(self):
        task_result = mommy.make(TaskResult, status='SUCCESS')
        file_from_system = "count/test/sample_zip_files/sample8.zip"
        zipfile_name = file_from_system.split('/')[-1]
        obj_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, zipfile_name)
        first_file_obj = File(
            file=file_from_system,
            path=obj_path,
            display_name='sample8.zip',
            user=self.user,
            category=None,
            task_id=task_result.task_id
        )
        first_file_obj.save()

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # check the message {"non_field_errors": ["Change The Zip File Name!"]} :
        self.assertEqual(response.data['non_field_errors'], ["Change The Zip File Name!"])

    def test_celery_upload_file_exists_with_pending_status_unsuccessfully(self):
        task_result = mommy.make(TaskResult, status='PENDING')
        file_from_system = "count/test/sample_zip_files/sample8.zip"
        zipfile_name = file_from_system.split('/')[-1]
        obj_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, zipfile_name)
        first_file_obj = File(
            file=file_from_system,
            path=obj_path,
            display_name='sample8.zip',
            user=self.user,
            category=None,
            task_id=task_result.task_id
        )
        first_file_obj.save()

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # check the message {"non_field_errors": ["Change The Zip File Name!"]} :
        self.assertEqual(response.data['non_field_errors'], ["The Zip File Is Being Processed!"])

    def test_celery_upload_file_exists_with_failure_status_successfully(self):
        task_result = mommy.make(TaskResult, status='FAILURE')
        file_from_system = "count/test/sample_zip_files/sample8.zip"
        zipfile_name = file_from_system.split('/')[-1]
        obj_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, zipfile_name)
        first_file_obj = File(
            file=file_from_system,
            path=obj_path,
            display_name='sample8.zip',
            user=self.user,
            category=None,
            task_id=task_result.task_id
        )
        first_file_obj.save()

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], "The File Was Received.")
        new_file_obj = File.objects.filter(path=obj_path)
        self.assertEqual(new_file_obj.count(), 1)
        self.assertEqual(new_file_obj[0].task_id, response.data['task_id'])

