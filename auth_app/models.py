from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.core.validators import EmailValidator
from django.core.validators import RegexValidator


class DueñoManager(BaseUserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('El email es obligatorio')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(email, password, **extra_fields)


class Dueño(AbstractBaseUser):
    dueño_id = models.AutoField(primary_key=True)
    nombre = models.CharField(max_length=100)
    email = models.EmailField(unique=True, validators=[EmailValidator()])
    ubicación = models.CharField(max_length=255)  # Formato: "lat,lng"
    fecha_registro = models.DateTimeField(auto_now_add=True)
    
    # Campo password mapeado a contraseña en la BD
    password = models.CharField(max_length=255, db_column='contraseña')
    
    # Campos requeridos por AbstractBaseUser pero opcionales en la BD
    last_login = models.DateTimeField(null=True, blank=True, db_column='last_login')
    
    # Campos de perfil (agregados directamente a la tabla dueños)
    foto_perfil = models.CharField(max_length=255, blank=True, null=True)
    telefono = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        validators=[RegexValidator(
            regex=r'^\+?1?\d{9,15}$',
            message="El teléfono debe tener entre 9 y 15 dígitos."
        )]
    )
    biografia = models.TextField(blank=True, null=True, max_length=500)
    fecha_nacimiento = models.DateField(blank=True, null=True)
    genero = models.CharField(
        max_length=20,
        choices=[
            ('Masculino', 'Masculino'),
            ('Femenino', 'Femenino'),
            ('Otro', 'Otro'),
            ('Prefiero no decir', 'Prefiero no decir'),
        ],
        blank=True,
        null=True
    )
    ciudad = models.CharField(max_length=100, blank=True, null=True)
    estado = models.CharField(max_length=100, blank=True, null=True)
    pais = models.CharField(max_length=100, blank=True, null=True)
    mostrar_telefono = models.BooleanField(default=False)
    mostrar_email = models.BooleanField(default=False)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    is_superuser = models.BooleanField(default=False)

    objects = DueñoManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['nombre']

    class Meta:
        db_table = 'dueños'
        indexes = [
            models.Index(fields=['ubicación'], name='idx_ubicacion'),
        ]

    def __str__(self):
        return f"{self.nombre} ({self.email})"
    
    def has_perm(self, perm, obj=None):
        return self.is_superuser
    
    def has_module_perms(self, app_label):
        return self.is_superuser


# El modelo Perfil ya no es necesario, los campos están en Dueño
# Se mantiene como clase proxy para compatibilidad con el código existente
class Perfil:
    """Proxy para acceder a los campos de perfil que están en Dueño"""
    pass


class BitacoraEvento(models.Model):
    """Bitácora de eventos de seguridad y acciones relevantes."""

    ACCIONES = [
        ('login_ok', 'Login exitoso'),
        ('login_fallo', 'Login fallido'),
        ('registro', 'Registro de usuario'),
        ('logout', 'Cierre de sesión'),
        ('oauth_google', 'Login con Google'),
        ('oauth_facebook', 'Login con Facebook'),
        ('perfil_actualizado', 'Perfil actualizado'),
        ('mascota_creada', 'Mascota creada'),
        ('mascota_eliminada', 'Mascota eliminada'),
        ('like_enviado', 'Like enviado'),
        ('match_formado', 'Match formado'),
        ('mensaje_enviado', 'Mensaje enviado'),
        ('acceso_denegado', 'Acceso denegado'),
    ]

    evento_id = models.AutoField(primary_key=True)
    accion = models.CharField(max_length=30, choices=ACCIONES)
    usuario = models.ForeignKey(
        'Dueño',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bitacora',
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    detalles = models.JSONField(default=dict, blank=True)
    fecha = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'bitacora_eventos'
        ordering = ['-fecha']
        indexes = [
            models.Index(fields=['accion'], name='idx_bitacora_accion'),
            models.Index(fields=['usuario'], name='idx_bitacora_usuario'),
            models.Index(fields=['fecha'], name='idx_bitacora_fecha'),
        ]

    def __str__(self):
        user = self.usuario.email if self.usuario else 'anónimo'
        return f"[{self.fecha}] {self.accion} — {user}"
