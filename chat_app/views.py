from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q
from django.shortcuts import get_object_or_404
from .models import Mensaje
from .serializers import MensajeSerializer, SendMessageSerializer
from matches_app.models import Match


class MensajeViewSet(viewsets.ModelViewSet):
    serializer_class = MensajeSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Mensaje.objects.filter(
            Q(match__mascota1__dueño=user) | Q(match__mascota2__dueño=user)
        )

    def list(self, request):
        """GET /api/chat/conversations/ → lista de conversaciones del usuario"""
        return self.conversations(request)

    @action(detail=False, methods=['get'])
    def conversations(self, request):
        """Obtener todas las conversaciones del usuario"""
        user = request.user
        
        # Obtener todos los matches aceptados donde el usuario participa
        matches = Match.objects.filter(
            Q(mascota1__dueño=user) | Q(mascota2__dueño=user),
            estado='Aceptado'
        )
        
        conversaciones = []
        for match in matches:
            # Determinar la otra mascota en el match
            if match.mascota1.dueño == user:
                otra_mascota = match.mascota2
                otro_dueño = match.mascota2.dueño
            else:
                otra_mascota = match.mascota1
                otro_dueño = match.mascota1.dueño
            
            # Obtener el último mensaje
            ultimo_mensaje = Mensaje.objects.filter(match=match).order_by('-fecha_envío').first()
            
            # Contar mensajes no leídos
            mensajes_no_leidos = Mensaje.objects.filter(
                match=match,
                leído=False
            ).exclude(remitente=user).count()
            
            from pets_app.serializers import MascotaSerializer
            conversaciones.append({
                'match_id': match.match_id,
                'otra_mascota': MascotaSerializer(otra_mascota, context={'request': request}).data,
                'otro_dueño': {
                    'dueño_id': otro_dueño.dueño_id,
                    'nombre': otro_dueño.nombre,
                    'email': otro_dueño.email
                },
                'ultimo_mensaje': MensajeSerializer(ultimo_mensaje).data if ultimo_mensaje else None,
                'mensajes_no_leidos': mensajes_no_leidos
            })
        
        return Response(conversaciones)

    @action(detail=True, methods=['get', 'post'], url_path='messages')
    def messages(self, request, pk=None):
        """Obtener todos los mensajes de una conversación (match) o enviar un mensaje"""
        match = get_object_or_404(Match, pk=pk, estado='Aceptado')
        
        # Verificar que el usuario participa en este match
        if match.mascota1.dueño != request.user and match.mascota2.dueño != request.user:
            return Response({'error': 'No tienes acceso a esta conversación'},
                          status=status.HTTP_403_FORBIDDEN)
        
        if request.method == 'GET':
            mensajes = Mensaje.objects.filter(match=match).order_by('fecha_envío')
            
            # Marcar mensajes como leídos
            Mensaje.objects.filter(
                match=match,
                leído=False
            ).exclude(remitente=request.user).update(leído=True)
            
            serializer = self.get_serializer(mensajes, many=True)
            return Response(serializer.data)
        
        elif request.method == 'POST':
            serializer = SendMessageSerializer(data=request.data)
            if serializer.is_valid():
                mensaje = Mensaje.objects.create(
                    match=match,
                    remitente=request.user,
                    contenido=serializer.validated_data['message']
                )
                return Response(MensajeSerializer(mensaje).data, status=status.HTTP_201_CREATED)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
