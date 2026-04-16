"""
Tests de seguridad para auth_app.
Cubre los casos del Plan de Pruebas de Seguridad (PT-AUTH-*, PT-RATE-*, PT-IDOR-*).
Ejecutar: pytest auth_app/tests.py -v
"""
from rest_framework import status
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase
from django.core.cache import cache
from .models import Dueño


def crear_usuario(email='user@test.com', password='Pass1234!', nombre='Test'):
    return Dueño.objects.create_user(
        email=email,
        password=password,
        nombre=nombre,
        ubicación='0,0',
    )


def obtener_token(user):
    token, _ = Token.objects.get_or_create(user=user)
    return token.key


class AuthTokenTests(APITestCase):
    """PT-AUTH-01 a PT-AUTH-06"""

    def setUp(self):
        cache.clear()
        self.user = crear_usuario()
        self.token = obtener_token(self.user)
        self.auth = {'HTTP_AUTHORIZATION': f'Bearer {self.token}'}

    # PT-AUTH-01
    def test_sin_token_devuelve_401(self):
        response = self.client.get('/api/pets/')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # PT-AUTH-06
    def test_token_invalido_devuelve_401_no_500(self):
        response = self.client.get('/api/pets/', HTTP_AUTHORIZATION='Bearer token_falso_abc')
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # PT-AUTH-04
    def test_token_invalidado_tras_logout(self):
        self.client.post('/api/auth/logout/', **self.auth)
        response = self.client.get('/api/pets/my-pets/', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # PT-AUTH-05
    def test_token_viejo_invalido_tras_nuevo_login(self):
        token_viejo = self.token
        self.client.post(
            '/api/auth/login/',
            {'email': 'user@test.com', 'password': 'Pass1234!'},
            format='json',
        )
        response = self.client.get(
            '/api/pets/my-pets/',
            HTTP_AUTHORIZATION=f'Bearer {token_viejo}',
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    # PT-AUTH-02
    def test_token_expirado_devuelve_401(self):
        from datetime import timedelta
        from django.utils import timezone
        token_obj = Token.objects.get(key=self.token)
        token_obj.created = timezone.now() - timedelta(days=8)
        token_obj.save()
        response = self.client.get('/api/pets/my-pets/', **self.auth)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class RegistroTests(APITestCase):
    """PT-IDOR-05 y validaciones de registro"""

    def setUp(self):
        cache.clear()

    def test_registro_exitoso(self):
        response = self.client.post(
            '/api/auth/register/',
            {'email': 'nuevo@test.com', 'password': 'Pass1234!', 'nombre': 'Nuevo', 'ubicación': '0,0'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)

    # PT-IDOR-05
    def test_registro_ignora_is_staff_y_is_superuser(self):
        self.client.post(
            '/api/auth/register/',
            {'email': 'hacker@test.com', 'password': 'Pass1234!', 'nombre': 'Hacker',
             'ubicación': '0,0', 'is_staff': True, 'is_superuser': True},
            format='json',
        )
        user = Dueño.objects.filter(email='hacker@test.com').first()
        self.assertIsNotNone(user)
        self.assertFalse(user.is_staff)
        self.assertFalse(user.is_superuser)

    def test_registro_sin_password_falla(self):
        response = self.client.post(
            '/api/auth/register/',
            {'email': 'sinpass@test.com', 'nombre': 'SinPass', 'ubicación': '0,0'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_registro_email_duplicado_falla(self):
        crear_usuario(email='dup@test.com')
        response = self.client.post(
            '/api/auth/register/',
            {'email': 'dup@test.com', 'password': 'Pass1234!', 'nombre': 'Dup', 'ubicación': '0,0'},
            format='json',
        )
        self.assertNotEqual(response.status_code, status.HTTP_201_CREATED)


class LoginTests(APITestCase):
    """PT-INFO-01 — enumeración de usuarios, login correcto/incorrecto"""

    def setUp(self):
        cache.clear()
        crear_usuario(email='existe@test.com', password='Pass1234!')

    def test_credenciales_invalidas_devuelve_400(self):
        response = self.client.post(
            '/api/auth/login/',
            {'email': 'existe@test.com', 'password': 'MalPassword'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_usuario_inexistente_mismo_codigo_de_error(self):
        """El mismo código de respuesta para email existente vs no existente evita enumeración."""
        response = self.client.post(
            '/api/auth/login/',
            {'email': 'noexiste_xyz@test.com', 'password': 'MalPassword'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_login_exitoso_devuelve_token(self):
        response = self.client.post(
            '/api/auth/login/',
            {'email': 'existe@test.com', 'password': 'Pass1234!'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('token', response.data)

    def test_password_no_aparece_en_respuesta(self):
        response = self.client.post(
            '/api/auth/login/',
            {'email': 'existe@test.com', 'password': 'Pass1234!'},
            format='json',
        )
        self.assertNotIn('password', response.data)
        self.assertNotIn('contraseña', response.data)


class SecurityHeadersTests(APITestCase):
    """PT-HDR-01 — cabeceras HTTP de seguridad"""

    def setUp(self):
        cache.clear()

    def test_cabeceras_seguridad_presentes(self):
        response = self.client.post('/api/auth/login/', {}, format='json')
        self.assertIn('X-Content-Type-Options', response)
        self.assertIn('X-Frame-Options', response)
        self.assertIn('Content-Security-Policy', response)
        self.assertIn('Referrer-Policy', response)
        self.assertEqual(response['X-Frame-Options'], 'DENY')
        self.assertEqual(response['X-Content-Type-Options'], 'nosniff')

    def test_sin_header_server_con_version(self):
        response = self.client.get('/api/auth/login/')
        # El servidor no debe revelar tecnología/versión
        server = response.get('Server', '')
        self.assertNotIn('Django', server)
        self.assertNotIn('Python', server)
