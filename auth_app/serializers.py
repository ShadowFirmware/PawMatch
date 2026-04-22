from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import Dueño, Perfil
import requests

UBICACION_FIELD = 'ubicación'


class PerfilSerializer(serializers.Serializer):
    """Serializer para los campos de perfil que están en Dueño"""
    nombre = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    email = serializers.EmailField(required=False, allow_null=True)
    ubicación = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    foto_perfil = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    telefono = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    biografia = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    fecha_nacimiento = serializers.DateField(required=False, allow_null=True)
    genero = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    ciudad = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    estado = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    pais = serializers.CharField(required=False, allow_null=True, allow_blank=True)
    mostrar_telefono = serializers.BooleanField(required=False, default=False)
    mostrar_email = serializers.BooleanField(required=False, default=False)


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
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

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
    access_token = serializers.CharField()

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
    access_token = serializers.CharField()

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
