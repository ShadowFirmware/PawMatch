from django.db import models
from matches_app.models import Match
from auth_app.models import Dueño


class Mensaje(models.Model):
    msg_id = models.AutoField(primary_key=True)
    match = models.ForeignKey(Match, on_delete=models.CASCADE, related_name='mensajes')
    remitente = models.ForeignKey(Dueño, on_delete=models.CASCADE, related_name='mensajes_enviados')
    contenido = models.TextField()
    fecha_envío = models.DateTimeField(auto_now_add=True)
    leído = models.BooleanField(default=False)

    class Meta:
        db_table = 'mensajes'
        ordering = ['fecha_envío']

    def __str__(self):
        return f"Mensaje de {self.remitente.nombre} en match {self.match.match_id}"
