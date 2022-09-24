from django.test import TestCase
from django.contrib.auth.models import User
from count.models import File, Status
from django.test.utils import override_settings
from model_mommy import mommy
from count.tasks import unzip
from django_celery_results.models import TaskResult
import pytest


class TaskTestCase(TestCase):
    def setUp(self):
        self.user = mommy.make(User, id=17)
        self.client.force_login(self.user)

    # test_file_db://  sqlite3://   memory://
    # @override_settings(CELERY_TASK_ALWAYS_EAGER=True,
    #                    CELERY_TASK_STORE_EAGER_RESULT=True,
    #                    BROKER_BACKEND='test_file_db://')
    # @pytest.mark.celery(CELERY_TASK_ALWAYS_EAGER=True,
    #                     CELERY_TASK_STORE_EAGER_RESULT=True,
    #                     BROKER_BACKEND='sqlite3://')
    def test_unzip_task_successfully(self):
        file_from_system = "count/test/sample_zip_files/sample3.zip"
        expected_zip_file_name = file_from_system.split('/')[-1]
        expected_zip_file_path = 'Documents/uploaded_files/user_{0}/{1}'.format(
            self.user.id, expected_zip_file_name
        )
        """save zip file object:"""
        zipfile_obj = File(
            file=file_from_system,
            path=expected_zip_file_path,
            display_name=expected_zip_file_name,
            user=self.user
        )
        zipfile_obj.save()
        """call task:"""
        db_zip_file = File.objects.get(category=None, display_name=expected_zip_file_name)
        unzip_task = unzip.apply(args=(db_zip_file.path, self.user.id))
        unzip_task_result = unzip_task.get()

        self.assertEqual(unzip_task_result['message'], 'successful Process')

        # task_result_obj = TaskResult.objects.get(task_id=unzip_task)
        # self.assertEqual(task_result_obj.status, 'SUCCESS')
        # self.assertEqual(task_result_obj.result, {"message": "successful Process"})
        # self.assertEqual(task_result_obj.child, {"children": []})

        self.assertEqual(unzip_task.status, 'SUCCESS')
        self.assertEqual(unzip_task.result, {"message": "successful Process"})
        self.assertEqual(unzip_task.children, None)

        