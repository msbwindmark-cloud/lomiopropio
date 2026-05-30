from django.shortcuts import render, redirect
from django.http import JsonResponse
from django.views.decorators.csrf import ensure_csrf_cookie
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.models import User
from django.contrib.auth.decorators import login_required
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
import os
import cv2
import numpy as np
from deepface import DeepFace
from django.conf import settings
from django.core.mail import send_mail
from .models import LogActividad
import csv
from django.http import HttpResponse
import glob


def registrar_log(request, accion, descripcion, usuario=None):
    """Función auxiliar para guardar trazas de auditoría"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    
    LogActividad.objects.create(
        usuario=usuario or (request.user if request.user.is_authenticated else None),
        accion=accion,
        descripcion=descripcion,
        ip_address=ip
    )

@ensure_csrf_cookie
def login_view(request):
    if request.user.is_authenticated:
        return redirect('dashboard')
        
    error_message = None
    if request.method == 'POST':
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        user = authenticate(request, username=user_name, password=pass_word)
        if user is not None:
            login(request, user)
            registrar_log(request, 'LOGIN_PASS', f'Usuario {user.username} entró con contraseña')
            return redirect('dashboard')
        else:
            registrar_log(request, 'ERROR', f'Intento de login fallido para: {user_name}')
            error_message = "Credenciales inválidas"
            
    return render(request, 'buscador_facial/login.html', {'error': error_message})


def registro_view(request):
    if request.method == 'POST':
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        rostro_file = request.FILES.get('rostro')
        
        if not all([user_name, pass_word, rostro_file]):
            return JsonResponse({'status': 'error', 'message': 'Faltan datos obligatorios'})
            
        if User.objects.filter(username=user_name).exists():
            return JsonResponse({'status': 'error', 'message': 'El usuario ya existe'})
            
        try:
            # 1. Crear usuario en Django
            user = User.objects.create_user(username=user_name, password=pass_word)
            
            # 2. Configurar rutas
            db_path = os.path.join(settings.MEDIA_ROOT, 'rostros_base')
            if not os.path.exists(db_path):
                os.makedirs(db_path, exist_ok=True)
                
            filename = f"{user_name}.jpg"
            file_path = os.path.join(db_path, filename)
            
            # --- SOLUCIÓN ROBUSTA PARA EL EFECTO ESPEJO ---
            # Leemos los bytes del archivo enviado
            rostro_bytes = rostro_file.read()
            
            # Convertimos los bytes crudos a un array de numpy
            nparr = np.frombuffer(rostro_bytes, np.uint8)
            
            # Decodificamos la imagen asegurando que OpenCV la entienda bien
            img_original = cv2.imdecode(nparr, cv2.IMREAD_UNCHANGED)
            
            if img_original is not None:
                # Si la imagen tiene canal Alfa (transparencia/PNG), lo quitamos o manejamos. 
                # Forzamos conversión a BGR estándar si viene en formato RGB de la web
                if len(img_original.shape) == 3 and img_original.shape[2] == 4:
                    img_original = cv2.cvtColor(img_original, cv2.COLOR_BGRA2BGR)
                
                # ¡Volteamos horizontalmente! (1)
                img_corregida = cv2.flip(img_original, 1)
                
                # Guardamos la imagen volteada en el disco
                cv2.imwrite(file_path, img_corregida)
            else:
                # Si falla la decodificación por el formato, la guardamos directa
                with open(file_path, 'wb+') as destination:
                    destination.write(rostro_bytes)
            # ----------------------------------------------
            
            # 3. Eliminar TODOS los archivos de caché .pkl de DeepFace
            archivos_pkl = glob.glob(os.path.join(db_path, '*.pkl'))
            for pkl_file in archivos_pkl:
                try:
                    os.remove(pkl_file)
                except: pass
                
            # 4. Enviar notificación por Email
            try:
                subject = f"Nuevo Registro Biométrico: {user_name}"
                message = f"Se ha registrado un nuevo usuario en el sistema.\n\nUsuario: {user_name}\nFecha: {user.date_joined}"
                from_email = settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'webmaster@localhost'
                recipient_list = getattr(settings, 'ADMIN_EMAIL_LIST', [])
                
                if recipient_list:
                    send_mail(subject, message, from_email, recipient_list, fail_silently=True)
            except Exception as mail_error:
                print(f"Error al enviar email: {mail_error}")

            registrar_log(request, 'REGISTRO', f'Nuevo usuario registrado: {user_name}', usuario=user)
            return JsonResponse({'status': 'success', 'message': '¡Registro completado con éxito!'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error al registrar: {str(e)}'})
            
    return render(request, 'buscador_facial/register.html')



def registro_view_old(request):
    if request.method == 'POST':
        user_name = request.POST.get('username')
        pass_word = request.POST.get('password')
        rostro_file = request.FILES.get('rostro')
        
        if not all([user_name, pass_word, rostro_file]):
            return JsonResponse({'status': 'error', 'message': 'Faltan datos obligatorios'})
            
        if User.objects.filter(username=user_name).exists():
            return JsonResponse({'status': 'error', 'message': 'El usuario ya existe'})
            
        try:
            # 1. Crear usuario en Django
            user = User.objects.create_user(username=user_name, password=pass_word)
            
            # 2. Guardar la foto en media/rostros_base/ con el nombre del usuario
            # Usamos el nombre del usuario para que DeepFace lo identifique automáticamente
            db_path = os.path.join(settings.MEDIA_ROOT, 'rostros_base')
            if not os.path.exists(db_path):
                os.makedirs(db_path, exist_ok=True)
                
            filename = f"{user_name}.jpg"
            file_path = os.path.join(db_path, filename)
            
            with open(file_path, 'wb+') as destination:
                for chunk in rostro_file.chunks():
                    destination.write(chunk)
            
            # 3. Eliminar el archivo .pkl de representación de DeepFace si existe
            # Esto obliga a DeepFace a recalcular la base de datos con el nuevo usuario
            pkl_path = os.path.join(db_path, 'representations_facenet.pkl')
            if os.path.exists(pkl_path):
                os.remove(pkl_path)
                
            # 4. Enviar notificación por Email
            try:
                subject = f"Nuevo Registro Biométrico: {user_name}"
                message = f"Se ha registrado un nuevo usuario en el sistema.\n\nUsuario: {user_name}\nFecha: {user.date_joined}"
                from_email = settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'webmaster@localhost'
                recipient_list = getattr(settings, 'ADMIN_EMAIL_LIST', [])
                
                if recipient_list:
                    send_mail(subject, message, from_email, recipient_list, fail_silently=True)
            except Exception as mail_error:
                print(f"Error al enviar email: {mail_error}")

            registrar_log(request, 'REGISTRO', f'Nuevo usuario registrado: {user_name}', usuario=user)
            return JsonResponse({'status': 'success', 'message': '¡Registro completado con éxito!'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error al registrar: {str(e)}'})
            
    return render(request, 'buscador_facial/register.html')

@login_required
def dashboard(request):
    user_photo_url = None
    photo_filename = f"{request.user.username}.jpg"
    photo_path = os.path.join(settings.MEDIA_ROOT, 'rostros_base', photo_filename)
    
    if os.path.exists(photo_path):
        user_photo_url = f"{settings.MEDIA_URL}rostros_base/{photo_filename}"
    
    # Obtener últimos 5 logs para el feed de seguridad
    ultimos_logs = LogActividad.objects.all()[:5]
    
    # Obtener el último log de este usuario para sacar su última emoción
    ultimo_login = LogActividad.objects.filter(usuario=request.user, accion='LOGIN_FACIAL').first()
    
    # Obtener últimos 5 intrusos
    intruder_path = os.path.join(settings.MEDIA_ROOT, 'intrusos')
    intrusos = []
    if os.path.exists(intruder_path):
        files = sorted(os.listdir(intruder_path), reverse=True)[:4]
        for f in files:
            intrusos.append({
                'url': f"{settings.MEDIA_URL}intrusos/{f}",
                'name': f
            })

    return render(request, 'buscador_facial/dashboard.html', {
        'user_photo': user_photo_url,
        'logs': ultimos_logs,
        'ultimo_login': ultimo_login,
        'intrusos': intrusos
    })

def logout_view(request):
    if request.user.is_authenticated:
        registrar_log(request, 'LOGOUT', f'Usuario {request.user.username} cerró sesión')
    logout(request)
    return redirect('login')

def reconocer_rostro(request):
    if request.method == 'POST' and request.FILES.get('imagen_camara'):
        try:
            imagen_file = request.FILES['imagen_camara']
            img_bytes = imagen_file.read()
            nparr = np.frombuffer(img_bytes, np.uint8)
            img = cv2.imdecode(nparr, cv2.IMREAD_COLOR)
            
            if img is None:
                return JsonResponse({'status': 'error', 'message': 'Captura fallida'})

            db_path = os.path.join(settings.MEDIA_ROOT, 'rostros_base')
            intruder_path = os.path.join(settings.MEDIA_ROOT, 'intrusos')
            if not os.path.exists(intruder_path):
                os.makedirs(intruder_path, exist_ok=True)

            if not os.path.exists(db_path) or not os.listdir(db_path):
                 return JsonResponse({'status': 'error', 'message': 'No hay rostros base configurados'})

            # Búsqueda con DeepFace (usando Facenet para evitar dlib)
            results = DeepFace.find(
                img_path=img, 
                db_path=db_path, 
                model_name='Facenet', 
                enforce_detection=True, 
                detector_backend='opencv'
            )
            
            # NUEVO: Análisis de Atributos (Emoción, Edad, Género)
            analisis = {}
            try:
                objs = DeepFace.analyze(img_path=img, actions=['age', 'gender', 'emotion'], enforce_detection=False)
                if objs:
                    item = objs[0]
                    analisis = {
                        'edad': item['age'],
                        'genero': item['dominant_gender'],
                        'emocion': item['dominant_emotion']
                    }
            except: pass

            if len(results) > 0 and not results[0].empty:
                mejor_match = results[0].iloc[0]
                ruta_match = mejor_match['identity']
                
                # Nombre del usuario = nombre del archivo
                nombre_usuario = os.path.basename(ruta_match).rsplit('.', 1)[0]
                
                try:
                    user = User.objects.get(username=nombre_usuario)
                    login(request, user)
                    registrar_log(request, 'LOGIN_FACIAL', f"LOGIN FACIAL EXITOSO: {user.username} (Attr: {analisis.get('emocion', 'N/A')})")
                    return JsonResponse({
                        'status': 'success',
                        'usuario': user.username,
                        'analisis': analisis,
                        'redirect': '/dashboard/'
                    })
                except User.DoesNotExist:
                    return JsonResponse({'status': 'error', 'message': f'Rostro de {nombre_usuario} reconocido, pero no tiene cuenta.'})
            else:
                # RECONOCIMIENTO FALLIDO: Guardar foto del intruso
                import time
                filename = f"intruso_{int(time.time())}.jpg"
                save_path = os.path.join(intruder_path, filename)
                cv2.imwrite(save_path, img)
                
                # Enviar Email de Alerta de Intruso
                try:
                    subject = "⚠️ ALERTA DE SEGURIDAD: Intento de Intrusión"
                    message = f"Se ha detectado un rostro no reconocido intentando acceder al sistema.\n\nEvidencia guardada: {filename}\nHora: {time.ctime()}\nIP: {request.META.get('REMOTE_ADDR')}"
                    recipient_list = getattr(settings, 'ADMIN_EMAIL_LIST', [])
                    if recipient_list:
                        send_mail(subject, message, settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'security@localhost', recipient_list, fail_silently=True)
                except: pass

                registrar_log(request, 'ERROR', f'Rostro no reconocido. Evidencia guardada: {filename}')
                return JsonResponse({'status': 'error', 'message': 'Rostro no reconocido. Intento registrado.'})
                
        except ValueError:
            return JsonResponse({'status': 'error', 'message': 'No se detectó rostro'})
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': f'Error: {str(e)}'})
            
    return JsonResponse({'status': 'error', 'message': 'Petición inválida'})

@login_required
def perfil_view(request):
    user = request.user
    if request.method == 'POST':
        new_username = request.POST.get('username')
        new_password = request.POST.get('password')
        new_photo = request.FILES.get('rostro')
        
        try:
            old_username = user.username
            db_path = os.path.join(settings.MEDIA_ROOT, 'rostros_base')
            
            # 1. Actualizar Username y Renombrar Foto
            if new_username and new_username != old_username:
                if User.objects.filter(username=new_username).exists():
                    return JsonResponse({'status': 'error', 'message': 'El nombre de usuario ya está en uso.'})
                
                # Renombrar archivo físico
                old_file = os.path.join(db_path, f"{old_username}.jpg")
                new_file = os.path.join(db_path, f"{new_username}.jpg")
                if os.path.exists(old_file):
                    os.rename(old_file, new_file)
                
                user.username = new_username
            
            # 2. Actualizar Password
            if new_password:
                user.set_password(new_password)
            
            # 3. Actualizar Foto (Sobrescribir)
            if new_photo:
                filename = f"{user.username}.jpg"
                file_path = os.path.join(db_path, filename)
                with open(file_path, 'wb+') as destination:
                    for chunk in new_photo.chunks():
                        destination.write(chunk)
                
                # Limpiar cache de DeepFace
                pkl_path = os.path.join(db_path, 'representations_facenet.pkl')
                if os.path.exists(pkl_path):
                    os.remove(pkl_path)
            
            user.save()
            
            if new_password:
                login(request, user)
            
            # 4. Registrar Log y enviar Email
            registrar_log(request, 'UPDATE_PERFIL', f'Usuario {user.username} actualizó su perfil')
            
            try:
                subject = f"Perfil Actualizado: {user.username}"
                message = f"El usuario {user.username} ha modificado sus datos de perfil o su firma biométrica.\n\nFecha: {user.date_joined}"
                from_email = settings.EMAIL_HOST_USER if hasattr(settings, 'EMAIL_HOST_USER') else 'webmaster@localhost'
                recipient_list = getattr(settings, 'ADMIN_EMAIL_LIST', [])
                if recipient_list:
                    send_mail(subject, message, from_email, recipient_list, fail_silently=True)
            except: pass

            return JsonResponse({'status': 'success', 'message': 'Perfil actualizado correctamente.'})
            
        except Exception as e:
            return JsonResponse({'status': 'error', 'message': str(e)})

    # Contexto para ver la foto actual
    photo_url = f"{settings.MEDIA_URL}rostros_base/{user.username}.jpg"
    return render(request, 'buscador_facial/profile.html', {'photo_url': photo_url})

@login_required
def export_logs(request):
    if not request.user.is_superuser:
        return HttpResponse("No autorizado", status=403)
        
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="logs_actividad.csv"'
    
    writer = csv.writer(response)
    writer.writerow(['Fecha/Hora', 'Usuario', 'Acción', 'Descripción', 'IP Address'])
    
    logs = LogActividad.objects.all()
    for log in logs:
        writer.writerow([log.fecha_hora, log.usuario, log.accion, log.descripcion, log.ip_address])
        
    return response
