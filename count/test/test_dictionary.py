from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from count.models import Dict


class DictTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = 'my_dict'
        cls.user = mommy.make(User, 3)
        cls.dict = mommy.make(Dict, 3)

        cls.dict[0].user.set(cls.user[0].id)
        cls.dict[1].user.set(cls.user[1].id)
        cls.dict[2].user.set(cls.user[2].id)
        cls.client.force_login(cls.user[0])

    def test_list_dictionary_successfully(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
