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
        file_from_system = "Documents/FileProject_samples/sample1.zip"
        file_from_project = 'Documents/uploaded_files/user_2/sample3.zip'

        # data = {"file": File(file_from_system)}
        # response = self.client.post(self.url, data, format='json')

        with open(file_from_project, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)

        # does the extracted file exist in the spesific path?
        # does the zip file save in the spesific path?

        # check the zip file was saved in DB :
        db_zip_file_query = File.objects.filter(category=None)
        self.assertEqual(db_zip_file_query.count(), 1)
        db_zip_file = db_zip_file_query[0]
        # self.assertEqual(db_zip_file.file, fp)
        # self.assertEqual(db_zip_file.path, file_from_project)
        self.assertEqual(db_zip_file.display_name, file_from_project.split('/')[-1])
        self.assertEqual(db_zip_file.user_id, self.user.id)
        self.assertEqual(db_zip_file.new, 0)
        self.assertEqual(db_zip_file.duplicate, 0)
        self.assertEqual(db_zip_file.typo, 0)

        # does the extracted file save in DB?

        # uploaded file's text files and folders be equal by text files and folders in DB (number and content)
