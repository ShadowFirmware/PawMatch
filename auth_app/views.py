import logging
from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action, throttle_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import Dueño
from .serializers import (
    DueñoSerializer, LoginSerializer, PerfilSerializer, 
    GoogleAuthSerializer, FacebookAuthSerializer,
    PasswordResetRequestSerializer, PasswordResetVerifySerializer, PasswordResetConfirmSerializer
)
from .audit import log_event
from .throttles import LoginRateThrottle, RegisterRateThrottle

logger = logging.getLogger('pawmatch.errors')

ERROR_CREAR_USUARIO = 'Error al crear usuario'
ERROR_INTERNO_SERVIDOR = 'Error interno del servidor'


class DueñoViewSet(viewsets.ModelViewSet):
    serializer_class = DueñoSerializer

    def get_permissions(self):
        # Solo crear cuenta (registro) es público; el resto requiere autenticación
        if self.action == 'create':
            return [AllowAny()]
        return [IsAuthenticated()]

    def get_queryset(self):
        # Cada usuario solo puede ver/modificar su propio registro
        return Dueño.objects.filter(pk=self.request.user.pk)

    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def mi_perfil(self, request):
        serializer = DueñoSerializer(request.user)
        return Response(serializer.data)

    @action(detail=False, methods=['put', 'patch'], permission_classes=[IsAuthenticated], url_path='actualizar_perfil')
    def actualizar_perfil(self, request):
        try:
            data = request.data.copy() if hasattr(request.data, 'copy') else dict(request.data)

            # Manejar foto de perfil como archivo multipart
            if 'photo' in request.FILES:
                from django.core.files.storage import default_storage
                import os
                photo_file = request.FILES['photo']
                ext = os.path.splitext(photo_file.name)[1].lower() or '.jpg'
                filename = f"perfiles/perfil_{request.user.pk}{ext}"
                path = default_storage.save(filename, photo_file)
                data['foto_perfil'] = f'/media/{path}'
            # Si foto_perfil viene como base64 ignorarla — excede max_length del campo
            elif 'foto_perfil' in data and isinstance(data.get('foto_perfil', ''), str) and data['foto_perfil'].startswith('data:'):
                del data['foto_perfil']

            serializer = PerfilSerializer(data=data, partial=True)
            if serializer.is_valid():
                dueno = request.user
                for field, value in serializer.validated_data.items():
                    setattr(dueno, field, value)
                dueno.save()
                log_event('perfil_actualizado', request=request)
                return Response({
                    'message': 'Perfil actualizado exitosamente',
                    'user': DueñoSerializer(dueno).data,
                })
            return Response({
                'error': 'Datos inválidos',
                'detail': serializer.errors,
            }, status=status.HTTP_400_BAD_REQUEST)
        except Exception:
            logger.exception('Error al actualizar perfil para usuario %s', request.user.pk)
            return Response(
                {'error': 'Error al actualizar perfil'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class PerfilViewSet(viewsets.ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        serializer = PerfilSerializer({
            'foto_perfil': request.user.foto_perfil,
            'telefono': request.user.telefono,
            'biografia': request.user.biografia,
            'fecha_nacimiento': request.user.fecha_nacimiento,
            'genero': request.user.genero,
            'ciudad': request.user.ciudad,
            'estado': request.user.estado,
            'pais': request.user.pais,
            'mostrar_telefono': request.user.mostrar_telefono,
            'mostrar_email': request.user.mostrar_email,
        })
        return Response(serializer.data)

    def update(self, request, pk=None):
        serializer = PerfilSerializer(data=request.data, partial=True)
        if serializer.is_valid():
            dueno = request.user
            for field, value in serializer.validated_data.items():
                setattr(dueno, field, value)
            dueno.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([LoginRateThrottle])
def login_view(request):
    serializer = LoginSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        user = serializer.validated_data['user']
        # Rotar token en cada login: eliminar el antiguo y crear uno nuevo
        Token.objects.filter(user=user).delete()
        token = Token.objects.create(user=user)
        log_event('login_ok', request=request, usuario=user)
        return Response({'token': token.key, 'user': DueñoSerializer(user).data})
    # Login fallido — no registrar el email para evitar enumeración de usuarios
    log_event('login_fallo', request=request)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Invalida el token del usuario en el servidor."""
    try:
        Token.objects.filter(user=request.user).delete()
        log_event('logout', request=request, usuario=request.user)
        return Response({'message': 'Sesión cerrada correctamente.'})
    except Exception:
        return Response({'error': 'Error al cerrar sesión.'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@throttle_classes([RegisterRateThrottle])
def register_view(request):
    try:
        serializer = DueñoSerializer(data=request.data)
        if serializer.is_valid():
            try:
                user = serializer.save()
                token, _ = Token.objects.get_or_create(user=user)
                log_event('registro', request=request, usuario=user)
                return Response(
                    {'token': token.key, 'user': DueñoSerializer(user).data},
                    status=status.HTTP_201_CREATED,
                )
            except Exception:
                logger.exception(ERROR_CREAR_USUARIO)
                return Response(
                    {'error': ERROR_CREAR_USUARIO},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
        return Response(
            {'error': 'Datos inválidos', 'detail': serializer.errors},
            status=status.HTTP_400_BAD_REQUEST,
        )
    except Exception:
        logger.exception('Error en register_view')
        return Response(
            {'error': ERROR_INTERNO_SERVIDOR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def google_auth_view(request):
    try:
        serializer = GoogleAuthSerializer(data=request.data)
        if serializer.is_valid():
            google_data = serializer.google_data
            email = google_data['email']
            nombre = google_data.get('name', email.split('@')[0])
            foto_url = google_data.get('picture', '')

            try:
                dueno = Dueño.objects.get(email=email)
                is_new_user = False
            except Dueño.DoesNotExist:
                try:
                    dueno = Dueño.objects.create_user(email=email, nombre=nombre, ubicación='0,0')
                    dueno.set_unusable_password()
                    if foto_url:
                        dueno.foto_perfil = foto_url
                    dueno.save()
                    is_new_user = True
                except Exception:
                    logger.exception(ERROR_CREAR_USUARIO)
                    return Response(
                        {'error': ERROR_CREAR_USUARIO},
                        status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    )

            token, _ = Token.objects.get_or_create(user=dueno)
            log_event('oauth_google', request=request, usuario=dueno, detalles={'new': is_new_user})
            return Response({
                'token': token.key,
                'user': DueñoSerializer(dueno).data,
                'is_new_user': is_new_user,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception('Error en google_auth_view')
        return Response(
            {'error': ERROR_INTERNO_SERVIDOR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def facebook_auth_view(request):
    try:
        serializer = FacebookAuthSerializer(data=request.data)
        if serializer.is_valid():
            fb_data = serializer.fb_data
            email = fb_data['email']
            nombre = fb_data.get('name', email.split('@')[0])
            foto_url = fb_data.get('picture', {}).get('data', {}).get('url', '')

            try:
                dueno = Dueño.objects.get(email=email)
                is_new_user = False
            except Dueño.DoesNotExist:
                dueno = Dueño.objects.create_user(email=email, nombre=nombre, ubicación='0,0')
                dueno.set_unusable_password()
                if foto_url:
                    dueno.foto_perfil = foto_url
                dueno.save()
                is_new_user = True

            token, _ = Token.objects.get_or_create(user=dueno)
            log_event('oauth_facebook', request=request, usuario=dueno, detalles={'new': is_new_user})
            return Response({
                'token': token.key,
                'user': DueñoSerializer(dueno).data,
                'is_new_user': is_new_user,
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception('Error en facebook_auth_view')
        return Response(
            {'error': ERROR_INTERNO_SERVIDOR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


# ── Recuperación de contraseña ───────────────────────────────────────────────

@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """Solicitar código de recuperación de contraseña."""
    try:
        serializer = PasswordResetRequestSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response({
                'message': 'Si el email existe, recibirás un código de recuperación.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception('Error en password_reset_request_view')
        return Response(
            {'error': ERROR_INTERNO_SERVIDOR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_verify_view(request):
    """Verificar código de recuperación."""
    try:
        serializer = PasswordResetVerifySerializer(data=request.data)
        if serializer.is_valid():
            return Response({
                'message': 'Código verificado correctamente.',
                'email': serializer.validated_data['email']
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception('Error en password_reset_verify_view')
        return Response(
            {'error': ERROR_INTERNO_SERVIDOR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """Confirmar nueva contraseña."""
    try:
        serializer = PasswordResetConfirmSerializer(data=request.data, context={'request': request})
        if serializer.is_valid():
            return Response({
                'message': 'Contraseña restablecida exitosamente.'
            }, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    except Exception:
        logger.exception('Error en password_reset_confirm_view')
        return Response(
            {'error': ERROR_INTERNO_SERVIDOR},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )
