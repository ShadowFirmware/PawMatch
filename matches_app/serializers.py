from rest_framework import serializers
from .models import Match, Reporte
from pets_app.serializers import MascotaSerializer


class MatchSerializer(serializers.ModelSerializer):
    mascota1_data = MascotaSerializer(source='mascota1', read_only=True)
    mascota2_data = MascotaSerializer(source='mascota2', read_only=True)

    class Meta:
        model = Match
        fields = [
            'match_id', 'mascota1', 'mascota2', 'mascota1_data',
            'mascota2_data', 'fecha_match', 'estado'
        ]
        read_only_fields = ['match_id', 'fecha_match']


class LikeMatchSerializer(serializers.Serializer):
    pet_id = serializers.IntegerField()
    target_pet_id = serializers.IntegerField()


class PassMatchSerializer(serializers.Serializer):
    pet_id = serializers.IntegerField()
    target_pet_id = serializers.IntegerField()


class ReporteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Reporte
        fields = ['report_id', 'dueño', 'mascota', 'motivo', 'fecha_reporte']
        read_only_fields = ['report_id', 'fecha_reporte']
