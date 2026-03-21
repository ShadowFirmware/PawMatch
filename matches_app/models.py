from django.db import models
from pets_app.models import Mascota


class Match(models.Model):
    ESTADO_CHOICES = [
        ('Pendiente', 'Pendiente'),
        ('Aceptado', 'Aceptado'),
        ('Rechazado', 'Rechazado'),
    ]

    match_id = models.AutoField(primary_key=True)
    mascota1 = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='matches_como_mascota1')
    mascota2 = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='matches_como_mascota2')
    fecha_match = models.DateTimeField(auto_now_add=True)
    estado = models.CharField(max_length=10, choices=ESTADO_CHOICES, default='Pendiente')

    class Meta:
        db_table = 'matches'
        unique_together = [['mascota1', 'mascota2']]

    def __str__(self):
        return f"Match entre {self.mascota1.nombre} y {self.mascota2.nombre}"


class Reporte(models.Model):
    report_id = models.AutoField(primary_key=True)
    dueño = models.ForeignKey('auth_app.Dueño', on_delete=models.CASCADE, related_name='reportes')
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='reportes')
    motivo = models.TextField()
    fecha_reporte = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'reportes'

    def __str__(self):
        return f"Reporte de {self.mascota.nombre} por {self.dueño.nombre}"
