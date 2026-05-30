# Sistema de Reconocimiento Facial con Django y DeepFace

He implementado la estructura solicitada, optimizada para procesamiento en memoria y utilizando la arquitectura de DeepFace con el modelo FaceNet.

## Estructura del Sistema

- **Backend**: Django 4.2+
- **Motor de IA**: DeepFace (con detector OpenCV y modelo FaceNet)
- **Procesamiento**: Las imágenes se reciben como BLOBs desde el frontend, se decodifican en memoria (NumPy/OpenCV) y se procesan sin guardar archivos temporales de captura en el disco.
- **Base de Datos Facial**: Localizada en `media/rostros_base/`.

## Archivos Principales

1.  [settings.py](file:///c:/practicarVB/deepface/core/settings.py): Configuración de `MEDIA_ROOT` y la app `buscador_facial`.
2.  [views.py](file:///c:/practicarVB/deepface/buscador_facial/views.py): Lógica de comparación biométrica.
3.  [index.html](file:///c:/practicarVB/deepface/buscador_facial/templates/buscador_facial/index.html): Interfaz de usuario con captura de webcam y AJAX.
4.  [requirements.txt](file:///c:/practicarVB/deepface/requirements.txt): Dependencias necesarias.

## Cómo Usar el Sistema

### 1. Preparar las Fotos de Referencia
Añade las fotos de las personas autorizadas a la carpeta `media/rostros_base/`.
- El nombre del archivo será el nombre que se muestre (ej: `juan_perez.jpg`).
- Asegúrate de que solo haya un rostro claro por foto.

### 2. Ejecutar el Servidor
```powershell
.\venv\Scripts\activate
python manage.py runserver
```

### 3. Acceder
Ve a `http://127.0.0.1:8000/` en tu navegador. 
- Permite el acceso a la cámara.
- Haz clic en "Identificar Rostro".

> [!TIP]
> La primera vez que realices una identificación, DeepFace descargará los pesos del modelo FaceNet (unos 90MB) y el pkl de la base de datos, por lo que tardará unos segundos extra.
