from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MascotaViewSet, FotoMascotaViewSet, PreferenciaViewSet

router = DefaultRouter()
router.register(r'pets', MascotaViewSet, basename='pet')
router.register(r'preferencias', PreferenciaViewSet, basename='preferencia')

# URLs para fotos anidadas
fotos_router = DefaultRouter()
fotos_router.register(r'fotos', FotoMascotaViewSet, basename='foto')

urlpatterns = [
    path('', include(router.urls)),
    path('pets/<int:mascota_pk>/', include(fotos_router.urls)),
]
