import re
from rest_framework import serializers
from .models import Mascota, FotoMascota, Preferencia


ALLOWED_IMAGE_TYPES = {'image/jpeg', 'image/png', 'image/gif', 'image/webp'}
ALLOWED_IMAGE_EXTENSIONS = {'.jpg', '.jpeg', '.png', '.gif', '.webp'}
MAX_PHOTO_SIZE = 5 * 1024 * 1024  # 5 MB


def sanitize_filename(name):
    """Reemplaza espacios y caracteres especiales para que el nombre sea URL-safe."""
    name = re.sub(r'\s+', '_', name)
    name = re.sub(r'[^\w\-.]', '', name)
    return name or 'foto'


def validate_photo(photo):
    """Valida tipo y tamaño de un archivo de foto. Lanza ValidationError si no pasa."""
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
            'mascota_id', 'dueño', 'dueño_nombre', 'dueño_email',
            'nombre', 'especie', 'raza', 'edad', 'género',
            'descripción', 'foto_url', 'fotos'
        ]
        read_only_fields = ['mascota_id', 'dueño']
        extra_kwargs = {
            'nombre': {'required': False},
            'especie': {'required': False},
            'raza': {'required': False},
            'edad': {'required': False},
            'género': {'required': False},
            'foto_url': {'required': False},
        }

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
        passthrough = ['nombre', 'especie', 'raza', 'edad', 'género', 'descripción', 'foto_url']

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
        if 'characteristics' in data and 'descripción' not in normalized:
            if hasattr(data, 'getlist'):
                # QueryDict (multipart/form-data): puede tener múltiples valores
                chars = data.getlist('characteristics')
            else:
                raw = data.get('characteristics', [])
                chars = raw if isinstance(raw, list) else [raw] if raw else []

            if chars:
                normalized['descripción'] = ', '.join(str(c) for c in chars if c)

        return super().to_internal_value(normalized)

    def create(self, validated_data):
        # Obtener archivo de foto desde request.FILES si existe
        request = self.context.get('request')
        photo = request.FILES.get('photo') if request else None

        # Validar límite de 5 mascotas por dueño
        dueño = validated_data.get('dueño')
        if dueño and Mascota.objects.filter(dueño=dueño).count() >= 5:
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
            'pref_id', 'dueño', 'especie_pref', 'edad_pref_min',
            'edad_pref_max', 'género_pref', 'distancia_max'
        ]
        read_only_fields = ['pref_id', 'dueño']
