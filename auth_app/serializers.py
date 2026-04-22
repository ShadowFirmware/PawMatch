from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Dueño, Perfil
from datetime import date
import re
import requests

UBICACION_FIELD = 'ubicación'
NOMBRE_REGEX = re.compile(r"^[a-zA-ZáéíóúüñÁÉÍÓÚÜÑ\s'\-]+$")


def validate_nombre_solo_letras(value):
    if value and not NOMBRE_REGEX.match(value.strip()):
        raise serializers.ValidationError('El nombre solo puede contener letras, espacios y guiones.')
    return value


class PerfilSerializer(serializers.Serializer):
    """Serializer para los campos de perfil que están en Dueño"""
    nombre     = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    email      = serializers.EmailField(required=False, allow_null=True, max_length=254)
    ubicación  = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=255)
    foto_perfil = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=255)
    telefono   = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=15)
    biografia  = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=500)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    genero     = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=20)
    ciudad     = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    estado     = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    pais       = serializers.CharField(required=False, allow_null=True, allow_blank=True, max_length=100)
    mostrar_telefono = serializers.BooleanField(required=False, default=False)
    mostrar_email    = serializers.BooleanField(required=False, default=False)

    def validate_nombre(self, value):
        return validate_nombre_solo_letras(value)

    def validate_fecha_nacimiento(self, value):
        if value:
            hoy = date.today()
            edad = hoy.year - value.year - ((hoy.month, hoy.day) < (value.month, value.day))
            if edad < 18:
                raise serializers.ValidationError('Debes tener al menos 18 años para registrarte.')
        return value


class DueñoSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=False, allow_blank=False)
    # Campos de perfil incluidos directamente
    perfil = serializers.SerializerMethodField()

    class Meta:
        model = Dueño
        fields = [
            'dueño_id', 'nombre', 'email', 'password', UBICACION_FIELD, 
            'fecha_registro', 'foto_perfil', 'telefono', 'biografia',
            'fecha_nacimiento', 'genero', 'ciudad', 'estado', 'pais',
            'mostrar_telefono', 'mostrar_email', 'perfil'
        ]
        extra_kwargs = {
            'password': {'write_only': True},
            'dueño_id': {'read_only': True},
            'fecha_registro': {'read_only': True},
            'nombre': {'required': True},
            'email': {'required': True},
            UBICACION_FIELD: {'required': True},
            'foto_perfil': {'required': False, 'allow_null': True},
            'telefono': {'required': False, 'allow_null': True},
            'biografia': {'required': False, 'allow_null': True},
            'fecha_nacimiento': {'required': False, 'allow_null': True},
            'genero': {'required': False, 'allow_null': True},
            'ciudad': {'required': False, 'allow_null': True},
            'estado': {'required': False, 'allow_null': True},
            'pais': {'required': False, 'allow_null': True},
        }
    
    def validate_nombre(self, value):
        return validate_nombre_solo_letras(value)

    def validate_fecha_nacimiento(self, value):
        if value:
            hoy = date.today()
            edad = hoy.year - value.year - ((hoy.month, hoy.day) < (value.month, value.day))
            if edad < 18:
                raise serializers.ValidationError('Debes tener al menos 18 años para registrarte.')
        return value

    def get_perfil(self, obj):
        """Retorna los campos de perfil como un objeto anidado"""
        return {
            'foto_perfil': obj.foto_perfil,
            'telefono': obj.telefono,
            'biografia': obj.biografia,
            'fecha_nacimiento': obj.fecha_nacimiento.isoformat() if obj.fecha_nacimiento else None,
            'genero': obj.genero,
            'ciudad': obj.ciudad,
            'estado': obj.estado,
            'pais': obj.pais,
            'mostrar_telefono': obj.mostrar_telefono,
            'mostrar_email': obj.mostrar_email,
        }

    def create(self, validated_data):
        password = validated_data.pop('password', None)
        
        # Validar que password esté presente para registro normal
        if not password:
            raise serializers.ValidationError({'password': 'La contraseña es obligatoria para el registro.'})
        
        try:
            # Crear usuario con contraseña
            dueno = Dueño.objects.create_user(
                password=password,
                email=validated_data.get('email'),
                nombre=validated_data.get('nombre'),
                ubicación=validated_data.get(UBICACION_FIELD, '0,0'),
            )
            
            # Actualizar campos de perfil si vienen en los datos
            campos_perfil = ['foto_perfil', 'telefono', 'biografia', 'fecha_nacimiento', 
                           'genero', 'ciudad', 'estado', 'pais', 'mostrar_telefono', 'mostrar_email']
            for campo in campos_perfil:
                if campo in validated_data:
                    setattr(dueno, campo, validated_data[campo])
            
            dueno.save()
            return dueno
        except Exception as e:
            raise serializers.ValidationError({'error': f'Error al crear usuario: {str(e)}'})


class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField(max_length=254)
    password = serializers.CharField(write_only=True, max_length=128)

    def validate(self, attrs):
        email = attrs.get('email')
        password = attrs.get('password')

        if email and password:
            user = authenticate(request=self.context.get('request'), email=email, password=password)
            if not user:
                raise serializers.ValidationError('Credenciales inválidas.')
            if not user.is_active:
                raise serializers.ValidationError('Usuario inactivo.')
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Debe proporcionar email y contraseña.')
        return attrs


class GoogleAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField(max_length=2048)

    def validate_access_token(self, value):
        """Validar el token de acceso de Google y obtener información del usuario"""
        try:
            response = requests.get(
                'https://www.googleapis.com/oauth2/v2/userinfo',
                params={'access_token': value}
            )

            if response.status_code != 200:
                raise serializers.ValidationError('Token de acceso inválido.')

            google_data = response.json()

            if 'email' not in google_data:
                raise serializers.ValidationError('No se pudo obtener el email de Google.')

            self.google_data = google_data
            return value
        except requests.RequestException:
            raise serializers.ValidationError('Error al verificar el token con Google.')


class FacebookAuthSerializer(serializers.Serializer):
    access_token = serializers.CharField(max_length=2048)

    def validate_access_token(self, value):
        """Validar el token de acceso de Facebook y obtener información del usuario"""
        try:
            response = requests.get(
                'https://graph.facebook.com/me',
                params={'fields': 'id,name,email,picture.type(large)', 'access_token': value}
            )

            if response.status_code != 200:
                raise serializers.ValidationError('Token de Facebook inválido.')

            fb_data = response.json()

            if 'error' in fb_data:
                raise serializers.ValidationError(fb_data['error'].get('message', 'Error de Facebook.'))

            if 'email' not in fb_data:
                raise serializers.ValidationError('Tu cuenta de Facebook no tiene email asociado. Usa otro método de inicio de sesión.')

            self.fb_data = fb_data
            return value
        except requests.RequestException:
            raise serializers.ValidationError('Error al verificar el token con Facebook.')


# ── Serializers de recuperación de contraseña ────────────────────────────────

class PasswordResetRequestSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate(self, data):
        from .password_reset_utils import generate_and_send_reset_code
        generate_and_send_reset_code(data['email'], self.context.get('request'))
        return data


class PasswordResetVerifySerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4, min_length=4)

    def validate(self, data):
        from .password_reset_utils import verify_reset_code
        if not verify_reset_code(data['email'], data['code']):
            raise serializers.ValidationError('Código inválido o expirado.')
        return data


class PasswordResetConfirmSerializer(serializers.Serializer):
    email = serializers.EmailField()
    code = serializers.CharField(max_length=4, min_length=4)
    new_password = serializers.CharField(min_length=8, write_only=True)

    def validate(self, data):
        from .password_reset_utils import reset_password
        if not reset_password(data['email'], data['code'], data['new_password'], self.context.get('request')):
            raise serializers.ValidationError('Código inválido o expirado.')
        return data
