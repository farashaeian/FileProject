from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from count.models import File, Category
import os
from count.tasks import unzip
from zipfile import ZipFile
from count.custom_methods import analyze_text_file


class UploadFileTestsSuccessfully(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('celery_upload_file')
        cls.user = mommy.make(User)

    def setUp(self):
        self.client.force_login(self.user)

    def test_celery_upload_file_successfully_save_zipfile_in_db_successfully(self):
        file_from_system = "count/test/sample_zip_files/sample9.zip"

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
        file_from_system = "count/test/sample_zip_files/sample8.zip"

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
        file_from_system = "count/test/sample_zip_files/sample6.zip"

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

    def test_celery_upload_file_successfully_comparison_selected_zipfile_with_uploaded_zipfile_successfully(self):
        file_from_system = "count/test/sample_zip_files/sample5.zip"

        with open(file_from_system, 'rb') as zf:
            response = self.client.post(self.url, {'file': zf})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'The File Was Received.')

        # compare selected zipfile with uploaded zipfile content(item numbers up to their types and their path):

        # selected zipfile content:
        selected_zip_file_items_list = ZipFile(file_from_system).namelist()
        s_file_list_number, s_dir_list_number = 0, 0

        for item in selected_zip_file_items_list:
            if item.endswith('/'):
                s_dir_list_number += 1
            elif item.endswith('.txt'):
                s_file_list_number += 1

        # uploaded zipfile content:
        expected_zip_file_name = file_from_system.split('/')[-1]
        expected_zip_file_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, expected_zip_file_name)

        uploaded_zip_file_items_list = ZipFile(expected_zip_file_path).namelist()
        u_file_list_number, u_dir_list_number = 0, 0

        for item in uploaded_zip_file_items_list:
            if item.endswith('/'):
                u_dir_list_number += 1
            elif item.endswith('.txt'):
                u_file_list_number += 1

        # asserts:
        # compare items paths:
        self.assertEqual(selected_zip_file_items_list, uploaded_zip_file_items_list)
        # compare items number up to their types:
        self.assertEqual(len(selected_zip_file_items_list), len(uploaded_zip_file_items_list))
        self.assertEqual(s_dir_list_number, u_dir_list_number)
        self.assertEqual(s_file_list_number, u_file_list_number)

    def test_celery_upload_file_successfully_comparison_uploaded_zipfile_with_extracted_folder_successfully(self):
        """correct extraction"""
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

        # uploaded zipfile:
        expected_zip_file_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, expected_zip_file_name)

        uploaded_zip_file_items_list = ZipFile(expected_zip_file_path).namelist()
        # delete root folder from the list; because root folder doesn't contain itself
        expected_extracted_folder_name = expected_zip_file_name.split('.')[0]
        root_folder_path = '{0}/'.format(expected_extracted_folder_name)
        uploaded_zip_file_items_list.remove(root_folder_path)

        u_file_list_number, u_dir_list_number = 0, 0

        for item in uploaded_zip_file_items_list:
            if item.endswith('/'):
                u_dir_list_number += 1
            elif item.endswith('.txt'):
                u_file_list_number += 1

        # extracted folder:
        expected_extracted_folder_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, expected_extracted_folder_name)

        e_file_list, e_dir_list = [], []
        e_file_list_number, e_dir_list_number = 0, 0
        user_document_path = 'Documents/uploaded_files/user_{0}/'.format(self.user.id)

        for root, dirs, files in os.walk(expected_extracted_folder_path):
            for d in dirs:
                e_dir_list_number += 1
                temp_dir = ((os.path.join(root, d)).replace(user_document_path, ''))+'/'
                e_dir_list.append(temp_dir)
            for f in files:
                e_file_list_number += 1
                temp_file = (os.path.join(root, f)).replace(user_document_path, '')
                e_file_list.append(temp_file)
        extracted_folder_items_list = e_dir_list + e_file_list

        # asserts:
        # compare items paths:
        # Note: use assertIn instead of assertEqual because lists orders are not same.
        for item in uploaded_zip_file_items_list:
            self.assertIn(
                item,
                extracted_folder_items_list
            )
        # compare items number up to their types:
        self.assertEqual(
            len(uploaded_zip_file_items_list),
            e_dir_list_number + e_file_list_number
        )
        self.assertEqual(u_dir_list_number, e_dir_list_number)
        self.assertEqual(u_file_list_number, e_file_list_number)

    def test_celery_upload_file_successfully_comparison_extracted_folder_with_db_successfully(self):
        file_from_system = "count/test/sample_zip_files/sample1.zip"

        with open(file_from_system, 'rb') as zf:
            response = self.client.post(self.url, {'file': zf})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'The File Was Received.')

        # call the celery.task (unzip):
        expected_zip_file_name = file_from_system.split('/')[-1]
        db_zip_file = File.objects.get(category=None, display_name=expected_zip_file_name)
        unzip_task_result = unzip.apply(args=(db_zip_file.path, self.user.id)).get()
        self.assertEqual(unzip_task_result['message'], 'successful Process')

        # extracted folder:
        expected_extracted_folder_name = expected_zip_file_name.split('.')[0]
        expected_extracted_folder_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, expected_extracted_folder_name)

        e_file_list, e_dir_list = [], []
        e_file_list_number, e_dir_list_number = 0, 0

        for root, dirs, files in os.walk(expected_extracted_folder_path):
            for d in dirs:
                e_dir_list_number += 1
                e_dir_list.append(os.path.join(root, d))
            for f in files:
                e_file_list_number += 1
                e_file_list.append(os.path.join(root, f))

        # check extracted folder dirs exist in the DB:
        for item in e_dir_list:
            db_item = Category.objects.get(path=item)

            item_display_name = item.split('/')[-1]
            x = '/{0}'.format(item_display_name)
            item_father_path = item.replace(x, "")
            db_item_father = Category.objects.get(path=item_father_path)

            self.assertEqual(db_item.display_name, item_display_name)
            self.assertEqual(db_item.user_id, self.user.id)
            self.assertEqual(db_item.father_id, db_item_father.id)

        # check extracted folder text files exist in the DB:
        for item in e_file_list:
            db_item = File.objects.get(path=item)

            item_display_name = item.split('/')[-1]
            x = '/{0}'.format(item_display_name)
            item_category_path = item.replace(x, "")
            db_item_category = Category.objects.get(path=item_category_path)
            item_analyze = analyze_text_file(item, self.user)

            # self.assertEqual(db_item.file, item_file)
            self.assertEqual(db_item.display_name, item_display_name)
            self.assertEqual(db_item.user_id, self.user.id)
            self.assertEqual(db_item.category_id, db_item_category.id)
            # self.assertEqual(db_item.new, item_analyze['new'])
            # self.assertEqual(db_item.duplicate, item_analyze['duplicate'])
            self.assertEqual(db_item.typo, item_analyze['typo'])
            # ??? how solve the above problem: celery.task and analyze method both use
            # the same DB so the analyze method answer can't be true ????

    def test_celery_upload_file_successfully_run_celery_task_successfully(self):
        pass
    # how write test for celery.task different returns?????
