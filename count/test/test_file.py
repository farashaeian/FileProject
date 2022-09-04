from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from count.models import File, Category
from zipfile import ZipFile
import os
from count.tasks import unzip

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
        zip_file_expected_path = 'Documents/uploaded_files/user_{0}/{1}'.format(self.user.id, zip_file_name)
        # ???? how handle system file name management????? (change the duplicate file name)
        # solve it ??? :
        # self.assertEqual(db_zip_file.file, zip_file_expected_path)
        self.assertEqual(db_zip_file.path, zip_file_expected_path)
        self.assertEqual(db_zip_file.display_name, zip_file_name)
        self.assertEqual(db_zip_file.user_id, self.user.id)
        self.assertEqual(db_zip_file.new, 0)
        self.assertEqual(db_zip_file.duplicate, 0)
        self.assertEqual(db_zip_file.typo, 0)

        # check the zip file was saved in the defined path :
        root_folder_path = 'Documents/uploaded_files/user_{0}'.format(self.user.id)
        file_list = []
        for root, dirs, files in os.walk(root_folder_path):
            for f in files:
                file_list.append(os.path.join(root, f))
        self.assertEqual(len(file_list), 1)
        self.assertEqual(file_list[0], db_zip_file.path)

        # call the celery.task (unzip):
        unzip_task_result = unzip.delay(db_zip_file.path, self.user.id)
        self.assertTrue(unzip_task_result.successful())

        # check the extracted folder was saved in DB:
        db_extracted_folder_query = Category.objects.filter(father=None)
        self.assertEqual(db_extracted_folder_query.count(), 1)
        db_extracted_folder = db_extracted_folder_query[0]
        extracted_folder_name = zip_file_name.split('.')[0]
        extracted_folder_expected_path = 'Documents/uploaded_files/user_{0}/{1}'.format(self.user.id, extracted_folder_name)
        self.assertEqual(db_extracted_folder.path, extracted_folder_expected_path)
        self.assertEqual(db_extracted_folder.display_name, extracted_folder_name)
        self.assertEqual(db_zip_file.user_id, self.user.id)

        # does the extracted file exist in the specific path?

        # uploaded zip file's text files and folders be equal by text files and folders in DB (number and content)
