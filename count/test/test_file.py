from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from count.models import File
from zipfile import ZipFile
from django.core.files import File as Filesystem


class FileTests(APITestCase):
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
        # check the {"non_field_errors": ["Uploaded File Is Not Zipped!"]}
        self.assertEqual(response.data['non_field_errors'][0], "Uploaded File Is Not Zipped!")

    def test_celery_upload_file_wrong_structure_unsuccessfully(self):
        file_from_system = "count/test/sample_zip_files/sample2.zip"

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # check the message {"non_field_errors": ["Invalid Items!"]}
        self.assertEqual(response.data['non_field_errors'], ["Invalid Items!"])

    def test_celery_upload_file_exists_unsuccessfully(self):
        obj_path = 'Documents/uploaded_files/user_{0}/sample8.zip'.format(self.user.id)
        first_file_obj = File(
            file=obj_path,
            path=obj_path,
            display_name='sample8.zip',
            user=self.user,
            category=None
        )
        first_file_obj.save()

        file_from_system = "count/test/sample_zip_files/sample8.zip"

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        # check the message {"non_field_errors": ["Change The Zip File Name!"]}
        self.assertEqual(response.data['non_field_errors'], ["Change The Zip File Name!"])

    def test_celery_upload_file_successfully(self):
        file_from_system = "count/test/sample_zip_files/sample5.zip"

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'The File Was Received.')

        # check the zip file was saved in DB :
        db_zip_file_query = File.objects.filter(category=None)
        self.assertEqual(db_zip_file_query.count(), 1)
        db_zip_file = db_zip_file_query[0]
        zip_file_name = file_from_system.split('/')[-1]
        expected_path = 'Documents/uploaded_files/user_{0}/{1}'.format(self.user.id, zip_file_name)
        # ???? how handle system file name management????? (change the duplicate file name)
        # self.assertEqual(db_zip_file.file, expected_path)
        self.assertEqual(db_zip_file.path, expected_path)
        self.assertEqual(db_zip_file.display_name, zip_file_name)
        self.assertEqual(db_zip_file.user_id, self.user.id)
        self.assertEqual(db_zip_file.new, 0)
        self.assertEqual(db_zip_file.duplicate, 0)
        self.assertEqual(db_zip_file.typo, 0)

        # does the extracted file exist in the spesific path?

        # does the zip file save in the spesific path?

        # does the extracted file save in DB?

        # uploaded file's text files and folders be equal by text files and folders in DB (number and content)
