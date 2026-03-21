from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from .models import Mascota, FotoMascota, Preferencia
from .serializers import MascotaSerializer, FotoMascotaSerializer, PreferenciaSerializer
from auth_app.models import Dueño


class MascotaViewSet(viewsets.ModelViewSet):
    serializer_class = MascotaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Mascota.objects.filter(dueño=user)

    def perform_create(self, serializer):
        serializer.save(dueño=self.request.user)

    @action(detail=False, methods=['get'], url_path='my-pets')
    def my_pets(self, request):
        """Obtener todas las mascotas del usuario autenticado"""
        mascotas = self.get_queryset()
        serializer = self.get_serializer(mascotas, many=True)
        return Response(serializer.data)


class FotoMascotaViewSet(viewsets.ModelViewSet):
    serializer_class = FotoMascotaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        mascota_id = self.kwargs.get('mascota_pk')
        return FotoMascota.objects.filter(mascota_id=mascota_id)

    def perform_create(self, serializer):
        mascota_id = self.kwargs.get('mascota_pk')
        mascota = get_object_or_404(Mascota, pk=mascota_id, dueño=self.request.user)
        serializer.save(mascota=mascota)


class PreferenciaViewSet(viewsets.ModelViewSet):
    serializer_class = PreferenciaSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return Preferencia.objects.filter(dueño=self.request.user)

    def perform_create(self, serializer):
        serializer.save(dueño=self.request.user)
