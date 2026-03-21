# 💬 Sistema de Chat con WebSockets - PawMatch

## 🚀 Configuración

El sistema de chat utiliza **Django Channels** con WebSockets para comunicación en tiempo real tipo WhatsApp.

### Instalación

```bash
pip install channels channels-redis
```

### Configuración para Producción

Para producción, se recomienda usar Redis como backend de Channels:

```python
# settings.py
CHANNEL_LAYERS = {
    'default': {
        'BACKEND': 'channels_redis.core.RedisChannelLayer',
        'CONFIG': {
            "hosts": [('127.0.0.1', 6379)],
        },
    },
}
```

## 🔌 Conexión WebSocket

### URL de Conexión

```
ws://localhost:8000/ws/chat/{match_id}/
```

### Autenticación

El WebSocket requiere autenticación mediante token. Puedes enviarlo de dos formas:

1. **En el header Authorization:**
   ```
   Authorization: Bearer {token}
   ```

2. **En el query string:**
   ```
   ws://localhost:8000/ws/chat/{match_id}/?token={token}
   ```

### Ejemplo de Conexión (JavaScript)

```javascript
const token = localStorage.getItem('token');
const matchId = 123;

// Opción 1: Token en query string
const ws = new WebSocket(`ws://localhost:8000/ws/chat/${matchId}/?token=${token}`);

// Opción 2: Token en header (requiere configuración adicional)
// Nota: Los navegadores no permiten headers personalizados en WebSocket
// Por lo que se recomienda usar query string o implementar autenticación en el servidor
```

## 📨 Tipos de Mensajes

### 1. Mensaje de Conexión (Servidor → Cliente)

Cuando te conectas exitosamente, recibirás:

```json
{
  "type": "connection",
  "message": "Conectado al chat",
  "match_id": 123
}
```

### 2. Enviar Mensaje (Cliente → Servidor)

Para enviar un mensaje:

```json
{
  "type": "chat_message",
  "message": "Hola, ¿cómo estás?",
  "match_id": 123
}
```

### 3. Recibir Mensaje (Servidor → Cliente)

Cuando recibes un mensaje:

```json
{
  "type": "chat_message",
  "message": "Hola, ¿cómo estás?",
  "sender_id": 5,
  "sender_name": "Juan Pérez",
  "match_id": 123,
  "msg_id": 456,
  "timestamp": "2026-03-15T10:30:00Z"
}
```

### 4. Indicador de Escritura (Cliente → Servidor)

Para indicar que estás escribiendo:

```json
{
  "type": "typing",
  "is_typing": true
}
```

### 5. Indicador de Escritura (Servidor → Cliente)

Cuando otro usuario está escribiendo:

```json
{
  "type": "typing",
  "user_id": 5,
  "user_name": "Juan Pérez",
  "is_typing": true
}
```

## 💻 Ejemplo Completo de Implementación

### Frontend (React)

```javascript
import { useEffect, useRef, useState } from 'react';

const ChatComponent = ({ matchId, token }) => {
  const [messages, setMessages] = useState([]);
  const [isTyping, setIsTyping] = useState(false);
  const wsRef = useRef(null);

  useEffect(() => {
    // Conectar WebSocket
    const ws = new WebSocket(
      `ws://localhost:8000/ws/chat/${matchId}/?token=${token}`
    );

    ws.onopen = () => {
      console.log('WebSocket conectado');
    };

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data);

      switch (data.type) {
        case 'connection':
          console.log('Conectado al chat:', data.message);
          break;

        case 'chat_message':
          setMessages(prev => [...prev, {
            id: data.msg_id,
            text: data.message,
            sender_id: data.sender_id,
            sender_name: data.sender_name,
            timestamp: data.timestamp,
          }]);
          break;

        case 'typing':
          setIsTyping(data.is_typing);
          break;

        default:
          console.log('Tipo de mensaje desconocido:', data.type);
      }
    };

    ws.onerror = (error) => {
      console.error('WebSocket error:', error);
    };

    ws.onclose = () => {
      console.log('WebSocket desconectado');
    };

    wsRef.current = ws;

    return () => {
      ws.close();
    };
  }, [matchId, token]);

  const sendMessage = (text) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'chat_message',
        message: text,
        match_id: matchId,
      }));
    }
  };

  const sendTypingIndicator = (typing) => {
    if (wsRef.current && wsRef.current.readyState === WebSocket.OPEN) {
      wsRef.current.send(JSON.stringify({
        type: 'typing',
        is_typing: typing,
      }));
    }
  };

  return (
    <div>
      {/* Renderizar mensajes */}
      {messages.map(msg => (
        <div key={msg.id}>
          <strong>{msg.sender_name}:</strong> {msg.text}
        </div>
      ))}
      
      {/* Indicador de escritura */}
      {isTyping && <div>Escribiendo...</div>}
      
      {/* Input para enviar mensaje */}
      <input
        onKeyPress={(e) => {
          if (e.key === 'Enter') {
            sendMessage(e.target.value);
            e.target.value = '';
          }
        }}
        onInput={(e) => {
          sendTypingIndicator(e.target.value.length > 0);
        }}
      />
    </div>
  );
};
```

## 🔒 Seguridad

1. **Autenticación Requerida**: Solo usuarios autenticados pueden conectarse
2. **Validación de Acceso**: Solo los dueños de las mascotas en el match pueden acceder al chat
3. **Match Aceptado**: Solo se puede chatear si el match está en estado "Aceptado"
4. **Persistencia**: Todos los mensajes se guardan en la base de datos

## 📊 Flujo de Datos

1. **Usuario A y Usuario B hacen match** → Match creado con estado "Aceptado"
2. **Usuario A se conecta al WebSocket** → `ws://localhost:8000/ws/chat/{match_id}/?token={token}`
3. **Usuario A envía mensaje** → Mensaje guardado en BD y broadcast al grupo
4. **Usuario B recibe mensaje** → Mensaje aparece en tiempo real
5. **Usuario B responde** → Proceso se repite

## 🐛 Troubleshooting

### Error: "Connection refused"
- Verifica que el servidor Django esté corriendo
- Verifica que Channels esté instalado correctamente
- Revisa los logs del servidor

### Error: "Invalid token"
- Verifica que el token sea válido
- Asegúrate de estar autenticado
- El token debe estar en el query string o header

### Los mensajes no se reciben
- Verifica que ambos usuarios estén conectados al mismo `match_id`
- Verifica que el match esté en estado "Aceptado"
- Revisa la consola del navegador para errores

## 📝 Notas

- Los mensajes se guardan automáticamente en la base de datos
- El historial de mensajes se puede obtener mediante la API REST
- El WebSocket es para mensajes en tiempo real
- Si el WebSocket falla, puedes usar la API REST como fallback
