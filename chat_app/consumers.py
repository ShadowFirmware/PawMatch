import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from rest_framework.authtoken.models import Token
from .models import Mensaje
from matches_app.models import Match

User = get_user_model()

AUTH_TIMEOUT = 5  # segundos para enviar el primer mensaje de autenticación


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f'chat_{self.match_id}'
        self.user = None
        self.authenticated = False

        # Aceptar la conexión antes de verificar el token
        # (los navegadores no permiten headers custom en WebSocket)
        await self.accept()

        # Programar cierre si no llega autenticación en AUTH_TIMEOUT segundos
        self._auth_timeout_task = asyncio.ensure_future(self._auth_timeout())

    async def _auth_timeout(self):
        """Cierra la conexión si no se autenticó a tiempo."""
        await asyncio.sleep(AUTH_TIMEOUT)
        if not self.authenticated:
            await self.close(code=4001)

    async def disconnect(self, close_code):
        if hasattr(self, '_auth_timeout_task'):
            self._auth_timeout_task.cancel()
        if self.authenticated:
            await self.channel_layer.group_discard(
                self.room_group_name,
                self.channel_name
            )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')

        # ── Primer mensaje: autenticación ─────────────────────────────────────
        if not self.authenticated:
            if message_type != 'authenticate':
                await self.close(code=4001)
                return

            token_key = data.get('token', '')
            self.user = await self.get_user_from_token(token_key)

            if not self.user:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Token inválido o expirado.',
                }))
                await self.close(code=4001)
                return

            has_access = await self.check_match_access(self.match_id, self.user)
            if not has_access:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Sin acceso a este chat.',
                }))
                await self.close(code=4003)
                return

            self.authenticated = True
            self._auth_timeout_task.cancel()

            await self.channel_layer.group_add(
                self.room_group_name,
                self.channel_name
            )

            await self.send(text_data=json.dumps({
                'type': 'connection',
                'message': 'Conectado al chat',
                'match_id': self.match_id,
            }))
            return

        # ── Mensajes normales (solo si ya autenticado) ────────────────────────
        if message_type == 'chat_message':
            message_text = data.get('message', '')
            match_id = data.get('match_id', self.match_id)

            if message_text:
                mensaje = await self.save_message(match_id, message_text, self.user)

                await self.channel_layer.group_send(
                    self.room_group_name,
                    {
                        'type': 'chat_message',
                        'message': message_text,
                        'sender_id': self.user.dueño_id,
                        'sender_name': self.user.nombre,
                        'match_id': match_id,
                        'msg_id': mensaje.msg_id,
                        'timestamp': mensaje.fecha_envío.isoformat(),
                    }
                )

        elif message_type == 'typing':
            await self.channel_layer.group_send(
                self.room_group_name,
                {
                    'type': 'typing_indicator',
                    'user_id': self.user.dueño_id,
                    'user_name': self.user.nombre,
                    'is_typing': data.get('is_typing', False),
                }
            )

    async def chat_message(self, event):
        await self.send(text_data=json.dumps({
            'type': 'chat_message',
            'message': event['message'],
            'sender_id': event['sender_id'],
            'sender_name': event['sender_name'],
            'match_id': event['match_id'],
            'msg_id': event['msg_id'],
            'timestamp': event['timestamp'],
        }))

    async def typing_indicator(self, event):
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'is_typing': event['is_typing'],
        }))

    @database_sync_to_async
    def get_user_from_token(self, token_key):
        from auth_app.models import TokenActividad
        try:
            token = Token.objects.select_related('user').get(key=token_key)

            now = timezone.now()
            expiry_days = getattr(settings, 'TOKEN_EXPIRY_DAYS', 7)
            inactivity_minutes = getattr(settings, 'INACTIVITY_TIMEOUT_MINUTES', 5)

            # Verificar expiración absoluta
            if now > token.created + timedelta(days=expiry_days):
                token.delete()
                return None

            # Verificar cierre por inactividad
            actividad, creada = TokenActividad.objects.get_or_create(token=token)
            if not creada:
                limite = now - timedelta(minutes=inactivity_minutes)
                if actividad.ultima_actividad < limite:
                    token.delete()
                    return None

            # Actualizar actividad al conectarse por WS
            TokenActividad.objects.filter(token=token).update(ultima_actividad=now)

            return token.user
        except Token.DoesNotExist:
            return None

    @database_sync_to_async
    def check_match_access(self, match_id, user):
        try:
            match = Match.objects.get(pk=match_id, estado='Aceptado')
            return match.mascota1.dueño == user or match.mascota2.dueño == user
        except Match.DoesNotExist:
            return False

    @database_sync_to_async
    def save_message(self, match_id, contenido, remitente):
        match = Match.objects.get(pk=match_id)
        mensaje = Mensaje.objects.create(
            match=match,
            remitente=remitente,
            contenido=contenido
        )
        return mensaje
