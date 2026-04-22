import re
from rest_framework import serializers
from .models import Mascota, FotoMascota, Preferencia


ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB

# Firmas de bytes mágicos de cada formato de imagen soportado.
# Detectan el tipo real del archivo independientemente del nombre/MIME declarado.
_MAGIC_SIGNATURES = [
    (b'\xff\xd8\xff', 'JPEG'),
    (b'\x89PNG\r\n\x1a\n', 'PNG'),
    (b'GIF87a', 'GIF'),
    (b'GIF89a', 'GIF'),
    # WEBP: cabecera RIFF????WEBP (bytes 0-3 y 8-11)
]

DUENO_FIELD = 'dueño'
GENERO_FIELD = 'género'
DESCRIPCION_FIELD = 'descripción'
UBICACION_FIELD = 'ubicación'


def sanitize_filename(name):
    """Reemplaza espacios y caracteres especiales para que el nombre sea URL-safe."""
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[^\w\-.]', '', name)
    return name or 'foto'


def _check_magic_bytes(photo):
    """
    Lee los primeros 12 bytes del archivo y verifica que correspondan a una
    imagen válida. Previene que archivos maliciosos renombrados pasen la
    validación solo por extensión o Content-Type declarado por el cliente.
    """
    header = photo.read(12)
    photo.seek(0)

    # Verificar firmas estándar (JPEG, PNG, GIF)
    for magic, _ in _MAGIC_SIGNATURES:
        if header.startswith(magic):
            return True

    # Verificar WEBP: bytes 0-3 = 'RIFF', bytes 8-11 = 'WEBP'
    if header[:4] == b'RIFF' and header[8:12] == b'WEBP':
        return True

    return False


def validate_photo(photo):
    """Valida tipo real (magic bytes), extensión, MIME y tamaño de una foto."""
    import os
    ext = os.path.splitext(photo.name)[1].lower()
    if ext not in ALLOWED_IMAGE_EXTENSIONS:
        raise serializers.ValidationError(
            f'Formato de imagen no permitido ({ext}). Usa: jpg, jpeg, png, gif o webp.'
        )
    content_type = getattr(photo, 'content_type', '')
    if content_type and content_type not in ALLOWED_IMAGE_TYPES:
        raise serializers.ValidationError(
            f'Tipo de archivo no permitido ({content_type}).'
        )
    if photo.size > MAX_PHOTO_SIZE:
        mb = photo.size / (1024 * 1024)
        raise serializers.ValidationError(
            f'La imagen es demasiado grande ({mb:.1f} MB). Máximo permitido: 5 MB.'
        )
    # Verificar firma real del archivo (magic bytes)
    if not _check_magic_bytes(photo):
        raise serializers.ValidationError(
            'El archivo no es una imagen válida.'
        )


class FotoMascotaSerializer(serializers.ModelSerializer):
    class Meta:
        model = FotoMascota
        fields = ['foto_id', 'foto_url', 'es_principal']


class MascotaSerializer(serializers.ModelSerializer):
    fotos = FotoMascotaSerializer(many=True, read_only=True)
    dueño_nombre = serializers.CharField(source='dueño.nombre', read_only=True)
    dueño_email = serializers.EmailField(source='dueño.email', read_only=True)
    foto_url = serializers.SerializerMethodField()

    def get_foto_url(self, obj):
        """Devuelve la URL absoluta de la foto, con el path URL-encoded."""
        from urllib.parse import quote
        raw = obj.foto_url or ''
        if not raw:
            return ''
        if raw.startswith('http'):
            return raw
        # URL-encode the path to handle spaces/special chars in existing filenames
        encoded = quote(raw, safe='/:')
        request = self.context.get('request')
        if request:
            return request.build_absolute_uri(encoded)
        # Fallback sin request
        from django.conf import settings
        base = getattr(settings, 'SITE_URL', 'http://localhost:8000')
        return f"{base}{encoded}"

    class Meta:
        model = Mascota
        fields = [
            'mascota_id', DUENO_FIELD, 'dueño_nombre', 'dueño_email',
            'nombre', 'especie', 'raza', 'edad', GENERO_FIELD,
            DESCRIPCION_FIELD, 'foto_url', UBICACION_FIELD, 'fotos'
        ]
        read_only_fields = ['mascota_id', DUENO_FIELD]
        extra_kwargs = {
            'nombre':    {'required': False},
            'especie':   {'required': False},
            'raza':      {'required': False, 'allow_blank': True},
            'edad':      {'required': False},
            GENERO_FIELD: {'required': False, 'max_length': 20},
            DESCRIPCION_FIELD: {'required': False, 'allow_blank': True, 'max_length': 500},
            'foto_url':  {'required': False},
            UBICACION_FIELD: {'required': False, 'allow_blank': True, 'max_length': 255},
        }

    def _extract_characteristics(self, data):
        """Extrae características del request data, manejando QueryDict y listas."""
        if hasattr(data, 'getlist'):
            return data.getlist('characteristics')
        raw = data.get('characteristics', [])
        if isinstance(raw, list):
            return raw
        if raw:
            return [raw]
        return []

    def to_internal_value(self, data):
        """
        Mapea los nombres de campos del frontend a los del modelo backend.
        El AddPetModal envía: name, type, breed, age, characteristics, photo
        El modelo espera:    nombre, especie, raza, edad, descripción, foto_url
        """
        # Mapeo de nombres frontend → backend
        field_map = {
            'name': 'nombre',
            'type': 'especie',
            'breed': 'raza',
            'age': 'edad',
        }

        # Campos backend que pasan directo
        passthrough = ['nombre', 'especie', 'raza', 'edad', GENERO_FIELD, DESCRIPCION_FIELD, 'foto_url', UBICACION_FIELD]

        normalized = {}

        # Aplicar mapeo de frontend a backend
        for frontend_key, backend_key in field_map.items():
            val = data.get(frontend_key)
            if val is not None and val != '':
                normalized[backend_key] = val

        # Copiar campos backend que vengan directamente
        for field in passthrough:
            if field in data and data[field] is not None:
                normalized[field] = data[field]

        # Manejar characteristics (array) → descripción (string)
        if 'characteristics' in data and DESCRIPCION_FIELD not in normalized:
            chars = self._extract_characteristics(data)
            if chars:
                normalized[DESCRIPCION_FIELD] = ', '.join(str(c) for c in chars if c)

        return super().to_internal_value(normalized)

    def create(self, validated_data):
        # Obtener archivo de foto desde request.FILES si existe
        request = self.context.get('request')
        photo = request.FILES.get('photo') if request else None

        # Validar límite de 5 mascotas por dueño
        dueno = validated_data.get(DUENO_FIELD)
        if dueno and Mascota.objects.filter(dueño=dueno).count() >= 5:
            raise serializers.ValidationError('No puedes registrar más de 5 mascotas por dueño.')

        mascota = Mascota(**validated_data)

        if photo:
            validate_photo(photo)
            from django.core.files.storage import default_storage
            safe_name = sanitize_filename(photo.name)
            path = default_storage.save(f'mascotas/{safe_name}', photo)
            mascota.foto_url = f'/media/{path}'

        mascota.save()
        return mascota

    def update(self, instance, validated_data):
        # Obtener archivo de foto desde request.FILES si existe
        request = self.context.get('request')
        photo = request.FILES.get('photo') if request else None

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if photo:
            validate_photo(photo)
            from django.core.files.storage import default_storage
            safe_name = sanitize_filename(photo.name)
            path = default_storage.save(f'mascotas/{safe_name}', photo)
            instance.foto_url = f'/media/{path}'

        instance.save()
        return instance


class PreferenciaSerializer(serializers.ModelSerializer):
    class Meta:
        model = Preferencia
        fields = [
            'pref_id', DUENO_FIELD, 'especie_pref', 'edad_pref_min',
            'edad_pref_max', 'género_pref', 'distancia_max'
        ]
        read_only_fields = ['pref_id', DUENO_FIELD]
