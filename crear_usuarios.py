import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from django.contrib.auth.models import User

# Crear un usuario de prueba si no existe
def create_test_user(username, password):
    if not User.objects.filter(username=username).exists():
        User.objects.create_user(username=username, password=password)
        print(f"Usuario '{username}' creado correctamente.")
    else:
        print(f"El usuario '{username}' ya existe.")

if __name__ == "__main__":
    create_test_user('admin', 'admin123')
    create_test_user('juan', 'juan123')
