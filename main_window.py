# main_window.py

from flask import Flask, render_template_string, Response, request
import cv2
import os
from core.gemini_process import generate_image_with_gemini
from PIL import Image
from io import BytesIO
import base64
import threading

app = Flask(__name__)

# Directorio para guardar las imágenes
image_dir = "assets/images"
os.makedirs(image_dir, exist_ok=True)

# Variables globales para la cámara y los hilos
cap = None
output_frame = None
lock = threading.Lock()
generated_image_bytes = None

def get_camera_feed():
    """Genera el feed de la cámara para la interfaz web."""
    global cap
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(0)
    
    while True:
        with lock:
            if not cap.isOpened():
                break
            ret, frame = cap.read()
            if not ret:
                break
            
            # Codifica el frame para transmitirlo en el HTML
            ret, buffer = cv2.imencode('.jpg', frame)
            frame = buffer.tobytes()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame + b'\r\n')
            
def generate_image_process(original_path):
    """
    Función que ejecuta el proceso de generación de imagen de Gemini en un hilo.
    """
    global generated_image_bytes
    print("Enviando foto a Gemini... Esto puede tomar unos segundos.")
    generated_image_bytes = generate_image_with_gemini(original_path)

@app.route('/')
def index():
    """Ruta principal que muestra la interfaz web."""
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Transformación Profesional Instantánea</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin: 0px; background-color: #FFFFFF; }
                header { display: flex; align-items: center; justify-content: space-between; background-color: #00B2EE; padding: 20px ; color: white; border: 5px solid #000000;}
                #header-logo { width: -20%; height: 50px; margin-left: 20px; }
                .header-title { flex-grow: 1; text-align: center; }
                .container { display: flex; justify-content: center; gap: 20px; margin-top: 20px; }
                .image-box { border: 10px solid #000000; padding: 10px; width: 620px; height: 540px; background-color: #304870; color: white; }
                #original_image  {  border: 5px solid #F5EF2C; width: 98%; height: -100%; object-fit: contain; }
                #generated_image {  border: 5px solid #F5EF2C; width: 98%; height: -100%; object-fit: contain; }
            </style>
        </head>
        <body>
            <header>
                <img id="header-logo" src="{{ url_for('static', filename='LogoSalesiana.png') }}">
                <div class="header-title">
                    <h1>Transformación Profesional Instantánea</h1>
                </div>
                <div></div>
            </header>
            <p>Presiona el botón "Capturar y Generar" para tomar una foto y transformarla.</p>
            
            <button onclick="captureAndGenerate()">Capturar y Generar</button>
            <button onclick="clearImages()">Limpiar</button>
            <br><br>
            
            <div class="container">
                <div class="image-box">
                    <h2>En Vivo</h2>
                    <img id="original_image" src="{{ url_for('video_feed') }}">
                </div>
                <div class="image-box">
                    <h2>Imagen Generada</h2>
                    <img id="generated_image" src="">
                </div>
            </div>

            <script>
                function captureAndGenerate() {
                    fetch('/capture', { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                document.getElementById('generated_image').src = data.generated_image_url;
                            } else {
                                alert('Error al generar la imagen: ' + data.message);
                            }
                        })
                        .catch(error => {
                            console.error('Error:', error);
                            alert('Ocurrió un error al procesar la solicitud.');
                        });
                }
                
                function clearImages() {
                     fetch('/clear', { method: 'POST' })
                        .then(response => response.json())
                        .then(data => {
                            if (data.status === 'success') {
                                document.getElementById('generated_image').src = "";
                            }
                        });
                }

                // Actualiza la imagen original sin recargar la página
                // La imagen de la webcam se transmite continuamente
                // y se muestra en la etiqueta <img>.
            </script>
        </body>
        </html>
    """)

@app.route('/video_feed')
def video_feed():
    """Ruta que transmite el video de la cámara en vivo."""
    return Response(get_camera_feed(),
                    mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/capture', methods=['POST'])
def capture():
    """
    Ruta que captura la foto de la cámara, la procesa con Gemini
    y devuelve la imagen generada.
    """
    global cap, output_frame, generated_image_bytes

    if cap is None or not cap.isOpened():
        return {"status": "error", "message": "No se pudo acceder a la cámara."}

    # Captura un solo frame
    ret, frame = cap.read()
    if not ret:
        return {"status": "error", "message": "No se pudo capturar el frame."}

    original_path = os.path.join(image_dir, "original.png")
    cv2.imwrite(original_path, frame)
    print(f"Foto original guardada en {original_path}")
    
    # Inicia el proceso de Gemini en un hilo separado para no bloquear la interfaz
    gemini_thread = threading.Thread(target=generate_image_process, args=(original_path,))
    gemini_thread.start()
    gemini_thread.join() # Espera a que termine el hilo para obtener el resultado

    if generated_image_bytes:
        generated_image_path = os.path.join(image_dir, "generated.png")
        generated_image_pil = Image.open(BytesIO(generated_image_bytes.data))
        generated_image_pil.save(generated_image_path)
        print(f"Imagen generada guardada en {generated_image_path}")

        # Codifica la imagen generada en base64 para mostrarla en el HTML
        encoded_image = base64.b64encode(generated_image_bytes.data).decode('utf-8')
        image_data_uri = f"data:image/png;base64,{encoded_image}"
        
        return {"status": "success", "generated_image_url": image_data_uri}
    else:
        return {"status": "error", "message": "No se pudo generar la imagen con Gemini."}

@app.route('/clear', methods=['POST'])
def clear_images():
    """Ruta para limpiar la imagen generada en la interfaz."""
    global generated_image_bytes
    generated_image_bytes = None
    try:
        os.remove(os.path.join(image_dir, "generated.png"))
    except FileNotFoundError:
        pass
    return {"status": "success"}

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', port=5000, debug=False)
    finally:
        if cap is not None:
            cap.release()