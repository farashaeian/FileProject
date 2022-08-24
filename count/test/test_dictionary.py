from model_mommy import mommy
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User
from count.models import Dict
from random import randint


class DictTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.url = reverse('my_dict')
        cls.user = mommy.make(User, 3)
        cls.dict = mommy.make(Dict, 20)

    def setUp(self):
        self.random_id = randint(1, 3)
        self.client.force_login(self.user[self.random_id])

    def test_list_dictionary_successfully(self):
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        current_user_dict = Dict.objects.filter(user=self.user[self.random_id]).order_by('-number')
        self.assertEqual(len(response.data), current_user_dict.count())
        for i in range(len(response.data)):
            self.assertEqual(response.data[i]['word'], current_user_dict[i].word)
            self.assertEqual(response.data[i]['user'], current_user_dict[i].user)
            self.assertEqual(response.data[i]['number'], current_user_dict[i].number)
        i, j = 0, 1
        while i != len(response.data):
            self.assertGreaterEqual(
                response.data[i]['number'],
                current_user_dict[i].number
            )
