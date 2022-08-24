from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth.models import User


class UserTests(APITestCase):
    def setUp(self):
        self.url = reverse('user_register')
        self.data = {'username': 'sima', 'password': '1234'}

    def test_create_user_successfully(self):
        response = self.client.post(self.url, self.data, formt='json')

        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        created_user = User.objects.all()
        self.assertEqual(created_user.count(), 1)
        self.assertEqual(response.data['username'], created_user[0].username)
        self.assertEqual(response.data['password'], created_user[0].password)

    def test_create_user_with_existence_username(self):
        first_user = User(username='sima', password=1234)
        first_user.save()
        response = self.client.post(self.url, self.data, formt='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        existence_user = User.objects.all()
        self.assertEqual(existence_user.count(), 1)
