from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MatchViewSet, ReporteViewSet

router = DefaultRouter()
router.register(r'matches', MatchViewSet, basename='match')
router.register(r'reportes', ReporteViewSet, basename='reporte')

urlpatterns = [
    path('', include(router.urls)),
]
