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
        from pets_app.serializers import MascotaSerializer
        for match in matches:
            # Determinar mi mascota y la otra mascota en el match
            if match.mascota1.dueño == user:
                mi_mascota   = match.mascota1
                otra_mascota = match.mascota2
                otro_dueño   = match.mascota2.dueño
            else:
                mi_mascota   = match.mascota2
                otra_mascota = match.mascota1
                otro_dueño   = match.mascota1.dueño

            # Obtener el último mensaje
            ultimo_mensaje = Mensaje.objects.filter(match=match).order_by('-fecha_envío').first()

            # Contar mensajes no leídos
            mensajes_no_leidos = Mensaje.objects.filter(
                match=match,
                leído=False
            ).exclude(remitente=user).count()

            conversaciones.append({
                'match_id':          match.match_id,
                'mi_mascota':        MascotaSerializer(mi_mascota,   context={'request': request}).data,
                'otra_mascota':      MascotaSerializer(otra_mascota, context={'request': request}).data,
                'otro_dueño': {
                    'dueño_id': otro_dueño.dueño_id,
                    'nombre':   otro_dueño.nombre,
                    'email':    otro_dueño.email,
                },
                'ultimo_mensaje':    MensajeSerializer(ultimo_mensaje).data if ultimo_mensaje else None,
                'mensajes_no_leidos': mensajes_no_leidos,
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

                # Broadcast al grupo WebSocket para que los receptores lo reciban en tiempo real
                try:
                    from channels.layers import get_channel_layer
                    from asgiref.sync import async_to_sync
                    channel_layer = get_channel_layer()
                    async_to_sync(channel_layer.group_send)(
                        f'chat_{match.match_id}',
                        {
                            'type': 'chat_message',
                            'message': mensaje.contenido,
                            'sender_id': request.user.dueño_id,
                            'sender_name': request.user.nombre,
                            'match_id': match.match_id,
                            'msg_id': mensaje.msg_id,
                            'timestamp': mensaje.fecha_envío.isoformat(),
                        }
                    )
                except Exception:
                    pass  # Si el channel layer no está disponible, la respuesta REST es suficiente

                return Response(MensajeSerializer(mensaje).data, status=status.HTTP_201_CREATED)

            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
