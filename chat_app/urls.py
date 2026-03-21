from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import MensajeViewSet

router = DefaultRouter()
router.register(r'chat/conversations', MensajeViewSet, basename='conversation')

urlpatterns = [
    path('', include(router.urls)),
]
