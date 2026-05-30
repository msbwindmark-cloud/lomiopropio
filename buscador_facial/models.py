from django.db import models
from django.contrib.auth.models import User

class LogActividad(models.Model):
    ACCIONES = (
        ('REGISTRO', 'Registro de Usuario'),
        ('LOGIN_FACIAL', 'Login Facial Exitoso'),
        ('LOGIN_PASS', 'Login Contraseña Exitoso'),
        ('UPDATE_PERFIL', 'Actualización de Perfil'),
        ('LOGOUT', 'Cierre de Sesión'),
        ('ERROR', 'Error en Sistema'),
    )

    usuario = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    accion = models.CharField(max_length=20, choices=ACCIONES)
    descripcion = models.TextField()
    fecha_hora = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    def __clstr__(self):
        return f"{self.fecha_hora} - {self.usuario} - {self.accion}"

    class Meta:
        verbose_name = "Log de Actividad"
        verbose_name_plural = "Logs de Actividad"
        ordering = ['-fecha_hora']
