import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
from .models import Mensaje
from matches_app.models import Match

User = get_user_model()


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.match_id = self.scope['url_route']['kwargs']['match_id']
        self.room_group_name = f'chat_{self.match_id}'
        
        # Obtener usuario del token
        token_key = None
        for header_name, header_value in self.scope.get('headers', []):
            if header_name == b'authorization' or header_name == b'Authorization':
                auth_header = header_value.decode('utf-8')
                if auth_header.startswith('Bearer '):
                    token_key = auth_header.split(' ')[1]
                    break
        
        # También verificar en query string
        if not token_key:
            query_string = self.scope.get('query_string', b'').decode('utf-8')
            if 'token=' in query_string:
                token_key = query_string.split('token=')[1].split('&')[0]
        
        if token_key:
            self.user = await self.get_user_from_token(token_key)
        else:
            self.user = None
        
        if not self.user:
            await self.close()
            return
        
        # Verificar que el usuario tiene acceso a este match
        has_access = await self.check_match_access(self.match_id, self.user)
        if not has_access:
            await self.close()
            return
        
        # Unirse al grupo de chat
        await self.channel_layer.group_add(
            self.room_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Enviar mensaje de conexión
        await self.send(text_data=json.dumps({
            'type': 'connection',
            'message': 'Conectado al chat',
            'match_id': self.match_id
        }))

    async def disconnect(self, close_code):
        # Salir del grupo de chat
        await self.channel_layer.group_discard(
            self.room_group_name,
            self.channel_name
        )

    async def receive(self, text_data):
        data = json.loads(text_data)
        message_type = data.get('type')
        
        if message_type == 'chat_message':
            message_text = data.get('message', '')
            match_id = data.get('match_id', self.match_id)
            
            if message_text:
                # Guardar mensaje en la base de datos
                mensaje = await self.save_message(match_id, message_text, self.user)
                
                # Enviar mensaje al grupo
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
            # Enviar señal de escritura
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
        # Enviar mensaje al WebSocket
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
        # Enviar indicador de escritura
        await self.send(text_data=json.dumps({
            'type': 'typing',
            'user_id': event['user_id'],
            'user_name': event['user_name'],
            'is_typing': event['is_typing'],
        }))

    @database_sync_to_async
    def get_user_from_token(self, token_key):
        try:
            token = Token.objects.get(key=token_key)
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
