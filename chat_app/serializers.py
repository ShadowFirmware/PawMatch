from rest_framework import serializers
from .models import Mensaje
from matches_app.serializers import MatchSerializer


class MensajeSerializer(serializers.ModelSerializer):
    remitente_nombre = serializers.CharField(source='remitente.nombre', read_only=True)
    match_data = MatchSerializer(source='match', read_only=True)

    class Meta:
        model = Mensaje
        fields = [
            'msg_id', 'match', 'match_data', 'remitente', 'remitente_nombre',
            'contenido', 'fecha_envío', 'leído'
        ]
        read_only_fields = ['msg_id', 'fecha_envío']


class SendMessageSerializer(serializers.Serializer):
    message = serializers.CharField(min_length=1, max_length=2000, trim_whitespace=True)
