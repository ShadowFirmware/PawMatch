from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator
from auth_app.models import Dueño


class Mascota(models.Model):
    GENERO_CHOICES = [
        ('Macho', 'Macho'),
        ('Hembra', 'Hembra'),
        ('Otro', 'Otro'),
    ]

    mascota_id = models.AutoField(primary_key=True)
    dueño = models.ForeignKey(Dueño, on_delete=models.CASCADE, related_name='mascotas')
    nombre = models.CharField(max_length=100)
    especie = models.CharField(max_length=50)
    raza = models.CharField(max_length=50, blank=True, default='')
    edad = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(30)])
    género = models.CharField(max_length=10, choices=GENERO_CHOICES, blank=True, default='Otro')
    descripción = models.TextField(blank=True, default='')
    foto_url = models.CharField(max_length=255, blank=True, default='')

    class Meta:
        db_table = 'mascotas'
        indexes = [
            models.Index(fields=['especie'], name='idx_especie'),
            models.Index(fields=['edad'], name='idx_edad'),
            models.Index(fields=['género'], name='idx_género'),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.especie})"

    def save(self, *args, **kwargs):
        # Validar límite de 5 mascotas por dueño
        if not self.pk:  # Solo al crear, no al actualizar
            mascotas_count = Mascota.objects.filter(dueño=self.dueño).count()
            if mascotas_count >= 5:
                raise ValueError('No puedes registrar más de 5 mascotas por dueño.')
        super().save(*args, **kwargs)


class FotoMascota(models.Model):
    foto_id = models.AutoField(primary_key=True)
    mascota = models.ForeignKey(Mascota, on_delete=models.CASCADE, related_name='fotos')
    foto_url = models.CharField(max_length=255)
    es_principal = models.BooleanField(default=False)

    class Meta:
        db_table = 'fotos_mascotas'

    def __str__(self):
        return f"Foto de {self.mascota.nombre}"


class Preferencia(models.Model):
    GENERO_PREF_CHOICES = [
        ('Macho', 'Macho'),
        ('Hembra', 'Hembra'),
        ('Indistinto', 'Indistinto'),
    ]

    pref_id = models.AutoField(primary_key=True)
    dueño = models.ForeignKey(Dueño, on_delete=models.CASCADE, related_name='preferencias')
    especie_pref = models.CharField(max_length=50)  # Ej: "Perro,Gato"
    edad_pref_min = models.IntegerField(blank=True, null=True, validators=[MinValueValidator(0)])
    edad_pref_max = models.IntegerField(blank=True, null=True, validators=[MaxValueValidator(30)])
    género_pref = models.CharField(max_length=10, choices=GENERO_PREF_CHOICES)
    distancia_max = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(15)])

    class Meta:
        db_table = 'preferencias'

    def __str__(self):
        return f"Preferencias de {self.dueño.nombre}"
