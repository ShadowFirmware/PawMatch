from rest_framework import viewsets, status
from rest_framework.decorators import api_view, action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.decorators import throttle_classes
from django.db.models import Q
from django.shortcuts import get_object_or_404
import math
from .models import Match, Reporte
from .serializers import (
    MatchSerializer, LikeMatchSerializer, PassMatchSerializer, ReporteSerializer
)
from pets_app.models import Mascota, Preferencia
from auth_app.models import Dueño
from auth_app.audit import log_event
from auth_app.throttles import ReporteRateThrottle

ESTADO_ACEPTADO = 'Aceptado'
ESTADO_PENDIENTE = 'Pendiente'
ESTADO_RECHAZADO = 'Rechazado'


def calcular_distancia(lat1, lon1, lat2, lon2):
    """Calcula la distancia entre dos puntos geográficos en kilómetros usando la fórmula de Haversine"""
    R = 6371  # Radio de la Tierra en kilómetros
    
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    
    a = (math.sin(dlat / 2) ** 2 +
         math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) *
         math.sin(dlon / 2) ** 2)
    c = 2 * math.asin(math.sqrt(a))
    
    return R * c


def calcular_compatibilidad_caracteristicas(mascota1, mascota2):
    """Calcula la compatibilidad basada en características (50% del peso)"""
    score = 0
    max_score = 5

    # Misma especie — base fundamental del match (peso alto)
    if mascota1.especie.lower() == mascota2.especie.lower():
        score += 2

    # Edad similar — energía compatible
    if mascota1.edad is not None and mascota2.edad is not None:
        edad_diff = abs(mascota1.edad - mascota2.edad)
        if edad_diff == 0:
            score += 1.5
        elif edad_diff <= 2:
            score += 1
        elif edad_diff <= 4:
            score += 0.5

    # Misma raza — bonus de afinidad
    if mascota1.raza and mascota2.raza and mascota1.raza.lower() == mascota2.raza.lower():
        score += 1

    # Personalidad/descripción similar — similitud Jaccard sobre palabras significativas
    if mascota1.descripción and mascota2.descripción:
        palabras1 = {w.lower() for w in mascota1.descripción.split() if len(w) > 3}
        palabras2 = {w.lower() for w in mascota2.descripción.split() if len(w) > 3}
        if palabras1 and palabras2:
            jaccard = len(palabras1 & palabras2) / len(palabras1 | palabras2)
            score += jaccard * 0.5  # Máximo 0.5 pts

    return (score / max_score) * 0.5  # 50% del peso total


def calcular_compatibilidad_ubicacion(dueño1_ubicacion, dueño2_ubicacion, distancia_max=50):
    """Calcula la compatibilidad basada en ubicación (50% del peso)"""
    try:
        lat1, lon1 = map(float, dueño1_ubicacion.split(','))
        lat2, lon2 = map(float, dueño2_ubicacion.split(','))

        distancia = calcular_distancia(lat1, lon1, lat2, lon2)

        # Si está fuera del rango máximo, retornar 0
        if distancia > distancia_max:
            return 0

        # Normalizar: ≤1km máximo, 1-30km escala media, 30-50km escala baja
        if distancia <= 1:
            return 0.5
        elif distancia <= 30:
            return 0.5 - ((distancia - 1) / 29) * 0.2
        else:
            return 0.3 - ((distancia - 30) / 20) * 0.3
    except (ValueError, AttributeError, TypeError):
        return 0


class MatchViewSet(viewsets.ModelViewSet):
    serializer_class = MatchSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        return Match.objects.filter(
            Q(mascota1__dueño=user) | Q(mascota2__dueño=user)
        )

    def _aplicar_filtros_preferencia(self, queryset, preferencia):
        """Aplica filtros de preferencia al queryset de mascotas."""
        if preferencia.especie_pref:
            especies = [e.strip() for e in preferencia.especie_pref.split(',')]
            queryset = queryset.filter(especie__in=especies)
        
        if preferencia.edad_pref_min is not None:
            queryset = queryset.filter(edad__gte=preferencia.edad_pref_min)
        if preferencia.edad_pref_max is not None:
            queryset = queryset.filter(edad__lte=preferencia.edad_pref_max)
        
        if preferencia.género_pref != 'Indistinto':
            queryset = queryset.filter(género=preferencia.género_pref)
        
        return queryset

    def _calcular_distancia_entre_mascotas(self, mascota1, mascota2):
        """Calcula la distancia entre dos mascotas basándose en la ubicación propia de cada mascota."""
        try:
            ub1 = (mascota1.ubicación or '').strip()
            ub2 = (mascota2.ubicación or '').strip()

            if ub1 in ('0,0', '0.0,0.0', '') or ub2 in ('0,0', '0.0,0.0', ''):
                return None

            lat1, lon1 = map(float, ub1.split(','))
            lat2, lon2 = map(float, ub2.split(','))
            return calcular_distancia(lat1, lon1, lat2, lon2)
        except (ValueError, AttributeError, TypeError):
            return None

    def _debe_omitir_mascota(self, mascota, otra_mascota):
        """Verifica si una mascota debe omitirse (ya interactuó o tiene match)."""
        ya_actue = Match.objects.filter(
            mascota1=mascota, mascota2=otra_mascota
        ).exists()
        ya_aceptado = Match.objects.filter(
            Q(mascota1=mascota, mascota2=otra_mascota) |
            Q(mascota1=otra_mascota, mascota2=mascota),
            estado=ESTADO_ACEPTADO
        ).exists()
        return ya_actue or ya_aceptado

    @action(detail=False, methods=['get'], url_path='potential/(?P<pet_id>[^/.]+)')
    def potential_matches(self, request, pet_id=None):
        """Obtener posibles matches para una mascota"""
        mascota = get_object_or_404(Mascota, pk=pet_id, dueño=request.user)
        
        # Obtener preferencias del dueño
        try:
            preferencia = Preferencia.objects.get(dueño=request.user)
            distancia_max = preferencia.distancia_max
        except Preferencia.DoesNotExist:
            distancia_max = 50  # Default temporal
        
        # Obtener todas las mascotas excepto las del usuario actual
        otras_mascotas = Mascota.objects.exclude(dueño=request.user).exclude(pk=pet_id)
        
        # Filtrar por preferencias si existen
        if 'preferencia' in locals():
            otras_mascotas = self._aplicar_filtros_preferencia(otras_mascotas, preferencia)
        
        # Calcular compatibilidad para cada mascota
        matches_potenciales = []
        for otra_mascota in otras_mascotas:
            if self._debe_omitir_mascota(mascota, otra_mascota):
                continue

            # ¿Esta mascota ya me dio like? → mostrarla primero con badge
            liked_me = Match.objects.filter(
                mascota1=otra_mascota, mascota2=mascota, estado=ESTADO_PENDIENTE
            ).exists()

            # Calcular compatibilidad
            compat_caracteristicas = calcular_compatibilidad_caracteristicas(mascota, otra_mascota)
            compat_ubicacion = calcular_compatibilidad_ubicacion(
                mascota.ubicación or '0,0',
                otra_mascota.ubicación or '0,0',
                distancia_max
            )
            score_total = compat_caracteristicas + compat_ubicacion

            # Calcular distancia y filtrar por rango
            distancia = self._calcular_distancia_entre_mascotas(mascota, otra_mascota)
            
            if distancia is None or distancia <= distancia_max:
                matches_potenciales.append({
                    'mascota': otra_mascota,
                    'score': score_total,
                    'distancia': round(distancia, 2) if distancia else None,
                    'liked_me': liked_me,
                })

        # Ordenar: primero los que ya dieron like, luego por score descendente
        matches_potenciales.sort(key=lambda x: (not x['liked_me'], -x['score']))

        # Serializar resultados
        from pets_app.serializers import MascotaSerializer
        resultados = []
        for match in matches_potenciales:
            mascota_data = MascotaSerializer(match['mascota'], context={'request': request}).data
            resultados.append({
                'mascota': mascota_data,
                'score': round(match['score'], 2),
                'distancia_km': match['distancia'],
                'liked_me': match['liked_me'],
            })
        
        return Response(resultados)

    @action(detail=False, methods=['post'])
    def like(self, request):
        """Dar like a una mascota"""
        serializer = LikeMatchSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        pet_id = serializer.validated_data['pet_id']
        target_pet_id = serializer.validated_data['target_pet_id']

        mascota1 = get_object_or_404(Mascota, pk=pet_id, dueño=request.user)
        mascota2 = get_object_or_404(Mascota, pk=target_pet_id)

        if mascota1 == mascota2:
            return Response({'error': 'No puedes hacer match contigo mismo'},
                            status=status.HTTP_400_BAD_REQUEST)

        # ¿Ya hay un match aceptado? Devolverlo directamente
        ya_aceptado = Match.objects.filter(
            Q(mascota1=mascota1, mascota2=mascota2) |
            Q(mascota1=mascota2, mascota2=mascota1),
            estado=ESTADO_ACEPTADO
        ).first()
        if ya_aceptado:
            return Response({'match': MatchSerializer(ya_aceptado).data, 'es_match': True})

        # ¿La otra mascota ya me dio like? → match mutuo
        like_previo = Match.objects.filter(
            mascota1=mascota2, mascota2=mascota1, estado=ESTADO_PENDIENTE
        ).first()
        if like_previo:
            like_previo.estado = ESTADO_ACEPTADO
            like_previo.save()
            # Limpiar duplicado inverso si existiera (datos viejos)
            Match.objects.filter(mascota1=mascota1, mascota2=mascota2).delete()
            log_event(
                'match_formado',
                request=request,
                usuario=request.user,
                detalles={'match_id': like_previo.match_id, 'mascota1': mascota1.mascota_id, 'mascota2': mascota2.mascota_id},
            )
            return Response({'match': MatchSerializer(like_previo).data, 'es_match': True})

        # ¿Ya di like yo antes? Reusar el registro (no crear duplicado)
        mi_like = Match.objects.filter(mascota1=mascota1, mascota2=mascota2).first()
        if mi_like:
            return Response({'match': MatchSerializer(mi_like).data, 'es_match': False})

        # Like nuevo unilateral
        match = Match.objects.create(
            mascota1=mascota1,
            mascota2=mascota2,
            estado='Pendiente'
        )
        log_event(
            'like_enviado',
            request=request,
            usuario=request.user,
            detalles={'match_id': match.match_id, 'mascota_origen': mascota1.mascota_id, 'mascota_destino': mascota2.mascota_id},
        )
        return Response({'match': MatchSerializer(match).data, 'es_match': False})

    @action(detail=False, methods=['post'], url_path='pass')
    def pass_match(self, request):
        """Pasar (rechazar) una mascota"""
        serializer = PassMatchSerializer(data=request.data)
        if serializer.is_valid():
            pet_id = serializer.validated_data['pet_id']
            target_pet_id = serializer.validated_data['target_pet_id']
            
            mascota1 = get_object_or_404(Mascota, pk=pet_id, dueño=request.user)
            mascota2 = get_object_or_404(Mascota, pk=target_pet_id)

            # No sobreescribir un match ya aceptado
            ya_aceptado = Match.objects.filter(
                Q(mascota1=mascota1, mascota2=mascota2) |
                Q(mascota1=mascota2, mascota2=mascota1),
                estado=ESTADO_ACEPTADO
            ).first()
            if ya_aceptado:
                return Response({'message': 'Ya tienes un match aceptado con esta mascota'})

            # Crear match rechazado para evitar mostrarlo de nuevo
            match, created = Match.objects.get_or_create(
                mascota1=mascota1,
                mascota2=mascota2,
                defaults={'estado': ESTADO_RECHAZADO}
            )

            if not created and match.estado != ESTADO_ACEPTADO:
                match.estado = ESTADO_RECHAZADO
                match.save()
            
            return Response({'message': 'Match rechazado'})
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    @action(detail=False, methods=['get'], url_path='my-pets-overview')
    def my_pets_overview(self, request):
        """Resumen por mascota del usuario: likes pendientes y matches aceptados."""
        from urllib.parse import quote as url_quote
        mis_mascotas = Mascota.objects.filter(dueño=request.user)

        result = []
        for mascota in mis_mascotas:
            likes_pendientes = Match.objects.filter(
                mascota2=mascota, estado=ESTADO_PENDIENTE
            ).count()
            matches_aceptados = Match.objects.filter(
                Q(mascota1=mascota) | Q(mascota2=mascota),
                estado=ESTADO_ACEPTADO
            ).count()

            foto = mascota.foto_url or ''
            if foto and not foto.startswith('http'):
                foto = request.build_absolute_uri(url_quote(foto, safe='/:'))

            result.append({
                'mascota_id': mascota.mascota_id,
                'nombre': mascota.nombre,
                'especie': mascota.especie,
                'raza': mascota.raza or '',
                'edad': mascota.edad,
                'foto_url': foto,
                'likes_pendientes': likes_pendientes,
                'matches_aceptados': matches_aceptados,
            })

        return Response(result)

    @action(detail=False, methods=['get'], url_path='all-matches')
    def all_matches(self, request):
        """Obtener todos los matches aceptados del usuario (todas sus mascotas)"""
        matches = self.get_queryset().filter(estado=ESTADO_ACEPTADO)
        serializer = self.get_serializer(matches, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'], url_path='my-matches/(?P<pet_id>[^/.]+)')
    def my_matches(self, request, pet_id=None):
        """Obtener todos los matches aceptados de una mascota"""
        mascota = get_object_or_404(Mascota, pk=pet_id, dueño=request.user)
        
        matches = Match.objects.filter(
            Q(mascota1=mascota) | Q(mascota2=mascota),
            estado=ESTADO_ACEPTADO
        )
        
        serializer = self.get_serializer(matches, many=True)
        return Response(serializer.data)


    @action(detail=False, methods=['get'], url_path='stats')
    def stats(self, request):
        """Estadísticas del usuario: matches, chats activos, likes recibidos, mascotas"""
        from pets_app.models import Mascota
        from chat_app.models import Mensaje

        user = request.user
        mis_mascotas_ids = list(
            Mascota.objects.filter(dueño=user).values_list('mascota_id', flat=True)
        )

        total_matches = Match.objects.filter(
            Q(mascota1__dueño=user) | Q(mascota2__dueño=user),
            estado=ESTADO_ACEPTADO
        ).count()

        # Chats activos = matches aceptados que tienen al menos un mensaje
        active_chats = Match.objects.filter(
            Q(mascota1__dueño=user) | Q(mascota2__dueño=user),
            estado=ESTADO_ACEPTADO,
            mensajes__isnull=False
        ).distinct().count()

        # Likes recibidos = mascota2 siempre es quien recibió el like,
        # independientemente de si sigue pendiente o ya se convirtió en match.
        likes_recibidos = Match.objects.filter(
            mascota2__dueño=user,
            estado__in=[ESTADO_PENDIENTE, ESTADO_ACEPTADO]
        ).count()

        total_mascotas = len(mis_mascotas_ids)

        return Response({
            'total_matches': total_matches,
            'active_chats': active_chats,
            'likes_recibidos': likes_recibidos,
            'total_mascotas': total_mascotas,
        })

    @action(detail=False, methods=['get'], url_path='activity')
    def activity(self, request):
        """Actividad reciente: matches, likes y mensajes recibidos."""
        from chat_app.models import Mensaje
        user = request.user
        limit = min(int(request.query_params.get('limit', 8)), 100)
        actividades = []

        # Matches aceptados
        matches_recientes = Match.objects.filter(
            Q(mascota1__dueño=user) | Q(mascota2__dueño=user),
            estado=ESTADO_ACEPTADO
        ).select_related('mascota1', 'mascota2').order_by('-fecha_match')[:limit]

        for match in matches_recientes:
            otra = match.mascota2 if match.mascota1.dueño == user else match.mascota1
            actividades.append({
                'id': f'match_{match.match_id}',
                'type': 'new_match',
                'nombre': otra.nombre,
                'foto': otra.foto_url or '',
                'timestamp': match.fecha_match.isoformat(),
                'mensaje': 'Nuevo match',
                'match_id': match.match_id,
            })

        # Likes recibidos pendientes
        likes = Match.objects.filter(
            mascota2__dueño=user,
            estado=ESTADO_PENDIENTE
        ).select_related('mascota1').order_by('-fecha_match')[:limit]

        for like in likes:
            actividades.append({
                'id': f'like_{like.match_id}',
                'type': 'like_received',
                'nombre': like.mascota1.nombre,
                'foto': like.mascota1.foto_url or '',
                'timestamp': like.fecha_match.isoformat(),
                'mensaje': 'te dio like',
                'match_id': like.match_id,
            })

        # Mensajes recibidos — un solo item por conversación (el último mensaje de cada match)
        from django.db.models import Max
        ultimos_ids = (
            Mensaje.objects.filter(
                Q(match__mascota1__dueño=user) | Q(match__mascota2__dueño=user)
            )
            .exclude(remitente=user)
            .values('match')
            .annotate(last_id=Max('msg_id'))
            .values_list('last_id', flat=True)
        )
        mensajes = (
            Mensaje.objects.filter(msg_id__in=ultimos_ids)
            .select_related('remitente', 'match')
            .order_by('-fecha_envío')[:limit]
        )

        for msg in mensajes:
            actividades.append({
                'id': f'msg_{msg.msg_id}',
                'type': 'message_received',
                'nombre': msg.remitente.nombre,
                'foto': msg.remitente.foto_perfil or '',
                'timestamp': msg.fecha_envío.isoformat(),
                'mensaje': 'te envió un mensaje',
                'match_id': msg.match.match_id,
                'leido': msg.leído,
            })

        actividades.sort(key=lambda x: x['timestamp'], reverse=True)
        return Response(actividades[:limit])


class ReporteViewSet(viewsets.ModelViewSet):
    serializer_class = ReporteSerializer
    permission_classes = [IsAuthenticated]

    def get_throttles(self):
        if self.action == 'create':
            return [ReporteRateThrottle()]
        return super().get_throttles()

    def get_queryset(self):
        return Reporte.objects.filter(dueño=self.request.user)

    def perform_create(self, serializer):
        serializer.save(dueño=self.request.user)
