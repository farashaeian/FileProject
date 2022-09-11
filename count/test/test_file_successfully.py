from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from count.models import File, Category
import os
from count.tasks import unzip
from zipfile import ZipFile


class FileTestsSuccessfully(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('celery_upload_file')
        cls.user = mommy.make(User)

    def setUp(self):
        self.client.force_login(self.user)

    def test_celery_upload_file_successfully_save_zipfile_in_db_successfully(self):
        file_from_system = "count/test/sample_zip_files/sample8.zip"

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
        """solve it ??? :"""
        # self.assertEqual(db_zip_file.file, zip_file_expected_path)
        self.assertEqual(db_zip_file.path, zip_file_expected_path)
        self.assertEqual(db_zip_file.display_name, zip_file_name)
        self.assertEqual(db_zip_file.user_id, self.user.id)
        self.assertEqual(db_zip_file.new, 0)
        self.assertEqual(db_zip_file.duplicate, 0)
        self.assertEqual(db_zip_file.typo, 0)

    def test_celery_upload_file_successfully_save_zipfile_in_expected_path_successfully(self):
        file_from_system = "count/test/sample_zip_files/sample5.zip"

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'The File Was Received.')

        # check the zip file was saved in the defined path :
        user_folder_path = 'Documents/uploaded_files/user_{0}'.format(self.user.id)
        file_list = []
        for root, dirs, files in os.walk(user_folder_path):
            for f in files:
                file_list.append(os.path.join(root, f))

        expected_zip_file_name = file_from_system.split('/')[-1]
        db_zip_file_expected_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, expected_zip_file_name)
        # self.assertEqual(len(file_list), 1)  """ is it important??? """
        self.assertIn(db_zip_file_expected_path, file_list)

        current_zipfile_number_in_path = 0
        for i in file_list:
            if i == db_zip_file_expected_path:
                current_zipfile_number_in_path += 1
        self.assertEqual(current_zipfile_number_in_path, 1)

    def test_celery_upload_file_successfully_save_root_folder_in_db_successfully(self):
        file_from_system = "count/test/sample_zip_files/sample4.zip"

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'The File Was Received.')

        # call the celery.task (unzip):
        expected_zip_file_name = file_from_system.split('/')[-1]
        db_zip_file = File.objects.get(category=None, display_name=expected_zip_file_name)
        unzip_task_result = unzip.apply(args=(db_zip_file.path, self.user.id)).get()
        self.assertEqual(unzip_task_result['message'], 'successful Process')

        # check the extracted folder was saved in DB:
        db_extracted_folder_query = Category.objects.filter(father=None)
        self.assertEqual(db_extracted_folder_query.count(), 1)
        db_extracted_folder = db_extracted_folder_query[0]
        zip_file_name = file_from_system.split('/')[-1]
        extracted_folder_expected_name = zip_file_name.split('.')[0]
        extracted_folder_expected_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, extracted_folder_expected_name)
        self.assertEqual(db_extracted_folder.path, extracted_folder_expected_path)
        self.assertEqual(db_extracted_folder.display_name, extracted_folder_expected_name)
        self.assertEqual(db_extracted_folder.user_id, self.user.id)

    def test_celery_upload_file_successfully_save_root_folder_in_expected_path_successfully(self):
        file_from_system = "count/test/sample_zip_files/sample3.zip"

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'The File Was Received.')

        # call the celery.task (unzip):
        expected_zip_file_name = file_from_system.split('/')[-1]
        db_zip_file = File.objects.get(category=None, display_name=expected_zip_file_name)
        unzip_task_result = unzip.apply(args=(db_zip_file.path, self.user.id)).get()
        self.assertEqual(unzip_task_result['message'], 'successful Process')

        # check the extracted file exist in the specific path:
        user_folder_path = 'Documents/uploaded_files/user_{0}'.format(self.user.id)
        folder_list = []
        for root, dirs, files in os.walk(user_folder_path):
            for f in dirs:
                folder_list.append(os.path.join(root, f))

        extracted_folder_expected_name = expected_zip_file_name.split('.')[0]
        extracted_folder_expected_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, extracted_folder_expected_name)
        # self.assertEqual(len(folder_list), 1)  """ is it important??? """
        self.assertIn(extracted_folder_expected_path, folder_list)

        current_folder_number_in_path = 0
        for i in folder_list:
            if i == extracted_folder_expected_path:
                current_folder_number_in_path += 1
        self.assertEqual(current_folder_number_in_path, 1)

    def test_celery_upload_file_successfully_correct_extraction(self):
        file_from_system = "count/test/sample_zip_files/sample7.zip"

        with open(file_from_system, 'rb') as fp:
            response = self.client.post(self.url, {'file': fp})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'The File Was Received.')

        # call the celery.task (unzip):
        expected_zip_file_name = file_from_system.split('/')[-1]
        db_zip_file = File.objects.get(category=None, display_name=expected_zip_file_name)
        unzip_task_result = unzip.apply(args=(db_zip_file.path, self.user.id)).get()
        self.assertEqual(unzip_task_result['message'], 'successful Process')

        # check the  zip file's content (text files and dirs) &
        # extracted folder content equality (number & path):
        zip_file_items_list = ZipFile(file_from_system).namelist()
        zip_file_folders_list = []
        zip_file_folders_number = 0
        zip_file_text_files_list = []
        zip_file_text_files_number = 0
        for item in zip_file_items_list:
            if item.endswith('/'):
                zip_file_folders_list.append(item)
                zip_file_folders_number += 1
            elif item.endswith(".txt"):
                zip_file_text_files_list.append(item)
                zip_file_text_files_number += 1

        extracted_folder_name = expected_zip_file_name.split('.')[0]
        extracted_folder_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, extracted_folder_name)
        extracted_folder_dir_list = []
        extracted_folder_dir_number = 0
        extracted_folder_text_file_list = []
        extracted_folder_text_file_number = 0
        for root, dirs, files in os.walk(extracted_folder_path):
            for d in dirs:
                extracted_folder_dir_list.append(os.path.join(root, d))
                extracted_folder_dir_number += 1
            for f in files:
                extracted_folder_text_file_list.append(os.path.join(root, f))
                extracted_folder_text_file_number += 1

        self.assertEqual(zip_file_folders_number-1, extracted_folder_dir_number)
        self.assertEqual(zip_file_text_files_number, extracted_folder_text_file_number)
        # check folders paths : paths need to be in same format
        # check text files paths : paths need to be in same format

    def test_celery_upload_file_successfully_correct_content_saving_in_db(self):
        pass
        # sample1
        # uploaded zip file's content (text files and folders) be equal by text files
        # and folders in DB (number and content)
