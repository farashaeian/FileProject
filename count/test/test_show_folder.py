from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from count.custom_methods import calculate_folder_info, custom_response
from django.contrib.auth.models import User
from count.models import File, Category
import os
from count.tasks import unzip
from zipfile import ZipFile


class ShowFolder(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.upload_zipfile_url = reverse('celery_upload_file')
        cls.user = mommy.make(User)

    def setUp(self):
        self.client.force_login(self.user)

    def test_show_folder_successfully(self):
        # 1st step: upload a zip file.
        file_from_system = "count/test/sample_zip_files/sample3.zip"

        with open(file_from_system, 'rb') as zf:
            response = self.client.post(self.upload_zipfile_url, {'file': zf})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'The File Was Received.')

        # call the celery.task (unzip):
        expected_zip_file_name = file_from_system.split('/')[-1]
        db_zip_file = File.objects.get(category=None, display_name=expected_zip_file_name)
        unzip_task_result = unzip.apply(args=(db_zip_file.path, self.user.id)).get()
        self.assertEqual(unzip_task_result['message'], 'successful Process')

        # 2nd step: call show_folder url to show the root folder of uploaded zipfile content.
        expected_extracted_folder_name = expected_zip_file_name.split('.')[0]
        root_folder_obj = Category.objects.get(
            father=None,
            display_name=expected_extracted_folder_name
        )

        url = reverse('show_folder', kwargs={'pk': root_folder_obj.id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        # 3th step: produce the response manually.
        response_list = []
        response_list.append(calculate_folder_info(root_folder_obj.path))
        answer = custom_response(root_folder_obj)
        if answer == []:
            pass
        else:
            response_list.append(answer)
        manually_response_data = response_list
        self.assertEqual(
            response.data,
            manually_response_data
        )

    def test_show_folder_unsuccessfully_with_inaccessible_folder_id(self):
        # 1st step: upload a zip file.
        file_from_system = "count/test/sample_zip_files/sample3.zip"

        with open(file_from_system, 'rb') as zf:
            response = self.client.post(self.upload_zipfile_url, {'file': zf})

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['message'], 'The File Was Received.')

        # call the celery.task (unzip):
        expected_zip_file_name = file_from_system.split('/')[-1]
        db_zip_file = File.objects.get(category=None, display_name=expected_zip_file_name)
        unzip_task_result = unzip.apply(args=(db_zip_file.path, self.user.id)).get()
        self.assertEqual(unzip_task_result['message'], 'successful Process')

        # 2nd step: call show_folder url to show the root folder of uploaded zipfile content.
        expected_extracted_folder_name = expected_zip_file_name.split('.')[0]
        root_folder_obj = Category.objects.get(
            father=None,
            display_name=expected_extracted_folder_name
        )
        inaccessible_folder_id = root_folder_obj.id+1
        url = reverse('show_folder', kwargs={'pk': inaccessible_folder_id})
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)
