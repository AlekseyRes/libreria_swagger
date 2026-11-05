from datetime import timedelta

from django.conf import settings
from django.test import TestCase
from rest_framework import status
from rest_framework.test import APITestCase

from .models import User


class UserApiTests(APITestCase):
    def setUp(self):
        self.admin = User.objects.create_superuser(
            email='admin@libreria.com',
            password='AdminPass123!',
            first_name='Admin',
        )
        self.other = User.objects.create_user(
            email='otro@libreria.com',
            password='OtroPass123!',
        )
        self.target = User.objects.create_user(
            email='target@libreria.com',
            password='TargetPass123!',
        )
        self.users_url = '/api/v1/auth/users/'
        self.me_url = '/api/v1/auth/me/'
        self.token_url = '/api/v1/auth/token/'

    def authenticate_admin(self):
        self.client.force_authenticate(user=self.admin)

    def test_token_obtain_with_email_and_password(self):
        response = self.client.post(
            self.token_url,
            {'email': 'admin@libreria.com', 'password': 'AdminPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)
        self.assertIn('refresh', response.data)

    def test_me_requires_authentication(self):
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user_without_password(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], self.other.email)
        self.assertNotIn('password', response.data)

    def test_users_list_requires_authentication(self):
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_users_list_forbidden_for_non_admin(self):
        self.client.force_authenticate(user=self.other)
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

    def test_admin_can_list_users_without_password(self):
        self.authenticate_admin()
        response = self.client.get(self.users_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data[0])

    def test_admin_can_retrieve_user_without_password(self):
        self.authenticate_admin()
        url = '{}{}/'.format(self.users_url, self.target.id)
        response = self.client.get(url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertNotIn('password', response.data)
        self.assertNotIn('pbkdf2_', str(response.data))

    def test_admin_can_create_user_and_password_is_hashed(self):
        self.authenticate_admin()
        payload = {
            'email': 'nuevo@libreria.com',
            'password': 'NuevoPass123!',
            'first_name': 'Nuevo',
            'telefono': '5551234567',
        }
        response = self.client.post(self.users_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertNotIn('password', response.data)
        user = User.objects.get(email='nuevo@libreria.com')
        self.assertTrue(user.check_password('NuevoPass123!'))
        self.assertNotEqual(user.password, 'NuevoPass123!')

    def test_create_user_without_password_fails(self):
        self.authenticate_admin()
        payload = {'email': 'sinpass@libreria.com'}
        response = self.client.post(self.users_url, payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

    def test_admin_can_update_user(self):
        self.authenticate_admin()
        url = '{}{}/'.format(self.users_url, self.target.id)
        response = self.client.put(
            url,
            {
                'email': self.target.email,
                'first_name': 'Actualizado',
                'telefono': '5550000000',
            },
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.target.refresh_from_db()
        self.assertEqual(self.target.first_name, 'Actualizado')
        self.assertNotIn('password', response.data)

    def test_patch_without_password_preserves_hash_for_other_user(self):
        self.authenticate_admin()
        original_hash = User.objects.get(pk=self.target.pk).password
        url = '{}{}/'.format(self.users_url, self.target.id)
        response = self.client.patch(
            url,
            {'first_name': 'Cambiado'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refreshed = User.objects.get(pk=self.target.pk)
        self.assertEqual(refreshed.password, original_hash)
        self.assertEqual(refreshed.first_name, 'Cambiado')
        self.assertNotIn('password', response.data)

    def test_patch_with_password_rehashes(self):
        self.authenticate_admin()
        original_hash = User.objects.get(pk=self.target.pk).password
        url = '{}{}/'.format(self.users_url, self.target.id)
        response = self.client.patch(
            url,
            {'password': 'NuevaPass123!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refreshed = User.objects.get(pk=self.target.pk)
        self.assertNotEqual(refreshed.password, original_hash)
        self.assertTrue(refreshed.check_password('NuevaPass123!'))
        self.assertNotEqual(refreshed.password, 'NuevaPass123!')

    def test_patch_with_empty_password_preserves_hash(self):
        self.authenticate_admin()
        original_hash = User.objects.get(pk=self.target.pk).password
        url = '{}{}/'.format(self.users_url, self.target.id)
        response = self.client.patch(
            url,
            {'password': ''},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        refreshed = User.objects.get(pk=self.target.pk)
        self.assertEqual(refreshed.password, original_hash)

    def test_patch_with_short_password_is_rejected(self):
        self.authenticate_admin()
        original_hash = User.objects.get(pk=self.target.pk).password
        url = '{}{}/'.format(self.users_url, self.target.id)
        response = self.client.patch(
            url,
            {'password': 'abc'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)
        refreshed = User.objects.get(pk=self.target.pk)
        self.assertEqual(refreshed.password, original_hash)

    def test_jwt_access_token_authenticates_me_endpoint(self):
        token_response = self.client.post(
            self.token_url,
            {'email': 'admin@libreria.com', 'password': 'AdminPass123!'},
            format='json',
        )
        self.assertEqual(token_response.status_code, status.HTTP_200_OK)
        access = token_response.data['access']

        self.client.credentials(HTTP_AUTHORIZATION='Bearer {}'.format(access))
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['email'], 'admin@libreria.com')
        self.assertNotIn('password', response.data)

    def test_swagger_ui_returns_200(self):
        response = self.client.get('/swagger/')
        self.assertEqual(response.status_code, status.HTTP_200_OK)

    def test_swagger_schema_returns_200(self):
        response = self.client.get('/swagger/?format=openapi')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['info']['title'], 'Librería API')

    def test_access_token_lifetime_is_60_minutes(self):
        self.assertEqual(
            settings.SIMPLE_JWT['ACCESS_TOKEN_LIFETIME'],
            timedelta(minutes=60),
        )


class UserModelTests(TestCase):
    def test_create_user_requires_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(email='', password='SomePass123!')

    def test_create_superuser_sets_flags(self):
        user = User.objects.create_superuser(
            email='super@libreria.com',
            password='SuperPass123!',
        )
        self.assertTrue(user.is_staff)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.check_password('SuperPass123!'))
        self.assertEqual(str(user), 'super@libreria.com')
