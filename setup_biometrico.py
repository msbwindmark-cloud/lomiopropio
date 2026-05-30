import os
import django

# Configurar entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User
from buscador_facial.models import LogActividad
from django.conf import settings

def setup():
    print("🚀 Iniciando configuración del Sistema Biométrico Pro...")

    # 1. Crear carpetas necesarias
    db_path = os.path.join(settings.MEDIA_ROOT, 'rostros_base')
    if not os.path.exists(db_path):
        os.makedirs(db_path, exist_ok=True)
        print(f"✅ Carpeta de rostros creada en: {db_path}")

    # 2. Crear Superusuario si no existe
    username = "admin"
    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(username, 'admin@ejemplo.com', 'admin123')
        print(f"✅ Superusuario '{username}' creado (Pass: admin123)")
    else:
        print(f"ℹ️ El usuario '{username}' ya existe.")

    # 3. Crear logs de bienvenida para que el Dashboard luzca profesional
    if LogActividad.objects.count() == 0:
        LogActividad.objects.create(
            accion='REGISTRO',
            descripcion='Sistema inicializado correctamente. Núcleo biométrico activo.',
            ip_address='127.0.0.1'
        )
        LogActividad.objects.create(
            accion='ERROR',
            descripcion='Intento de intrusión bloqueado (Simulación de seguridad)',
            ip_address='192.168.1.50'
        )
        print("✅ Logs de auditoría iniciales generados.")

    print("\n✨ ¡Configuración completada! Ahora puedes:")
    print("1. Ejecutar: python manage.py runserver")
    print("2. Entrar a http://127.0.0.1:8000")
    print("3. Loguearte con 'admin' / 'admin123' para ver tu nuevo HUD de seguridad.")

if __name__ == "__main__":
    setup()
