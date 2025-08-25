from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.conf import settings

class Usuario(AbstractUser):
    TIPO_USUARIO = (
        ('free', 'Free'),
        ('standar', 'Standar'),
        ('pro', 'Pro'),
        ('admin', 'Administrador'),
    )
    tipo_usuario = models.CharField(max_length=10, choices=TIPO_USUARIO, default='free')
    data_rexistro = models.DateTimeField(default=timezone.now)
    email = models.EmailField(unique=True)

    
    groups = models.ManyToManyField(
        'auth.Group',
        related_name='custom_usuario_groups',
        blank=True,
        help_text='The groups this user belongs to.',
        verbose_name='groups',
    )
    user_permissions = models.ManyToManyField(
        'auth.Permission',
        related_name='custom_usuario_permissions',
        blank=True,
        help_text='Specific permissions for this user.',
        verbose_name='user permissions',
    )

    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

    def __str__(self):
        return self.email
    
    def save(self, *args, **kwargs):
        
        self.email = self.email.lower()
        super().save(*args, **kwargs)
        
    @classmethod
    def create_from_social(cls, social_data):
        
        email = social_data.get('email').lower()
        first_name = social_data.get('first_name', '')
        last_name = social_data.get('last_name', '')
        
        
        try:
            user = cls.objects.get(email=email)
        except cls.DoesNotExist:
            user = cls.objects.create_user(
                email=email,
                username=email,  
                first_name=first_name,
                last_name=last_name,
                tipo_usuario='free',  
                is_active=True
            )
        return user

class Plan(models.Model):
    nome = models.CharField(max_length=50)
    prezo = models.DecimalField(max_digits=6, decimal_places=2)
    descricion = models.TextField(blank=True)
    stripe_price_id = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        verbose_name = 'Plan'
        verbose_name_plural = 'Plans'

    def __str__(self):
        return f"{self.nome} ({self.prezo}€/mes)"

class Subscricion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='subscricions')
    plan = models.ForeignKey(Plan, on_delete=models.SET_NULL, null=True)
    stripe_customer_id = models.CharField(max_length=50, blank=True, null=True)
    stripe_subscription_id = models.CharField(max_length=50, blank=True, null=True)
    status = models.CharField(max_length=20, blank=True)
    active = models.BooleanField(default=True)
    data_inicio = models.DateTimeField(default=timezone.now)
    data_fin = models.DateTimeField(null=True, blank=True)
    consultas_diarias = models.IntegerField(default=0)
    ultima_consulta = models.DateField(default=timezone.now)

    class Meta:
        verbose_name = 'Subscrición'
        verbose_name_plural = 'Subscricións'

    def __str__(self):
        return f"Subscrición de {self.usuario.email} - {self.plan.nome if self.plan else 'Sin plan'}"

class Informe(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='informes')
    url = models.URLField()
    puntuacion = models.FloatField(default=0)
    problemas = models.JSONField(default=dict)
    consello_ia = models.TextField(blank=True, default='')
    razonamiento = models.TextField(blank=True, default='')
    screenshot = models.URLField(blank=True, null=True)
    data = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = 'Informe'
        verbose_name_plural = 'Informes'

    def __str__(self):
        return f"Informe para {self.url} - {self.data}"
    
class Articulo(models.Model):
    titulo = models.CharField(max_length=200, null=False, blank=False)
    subtitulo = models.CharField(max_length=200, null=True, blank=True)
    cuerpo = models.TextField(null=False, blank=False)
    imagen = models.ImageField(upload_to='articulos/', null=True, blank=True)
    autor = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, limit_choices_to={'tipo_usuario': 'admin'})
    fecha_publicacion = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.titulo

    class Meta:
        ordering = ['-fecha_publicacion']