# main_window.py

from flask import Flask, render_template_string, Response, request, jsonify
import cv2
import os
from core.gemini_process import generate_image_with_gemini
from PIL import Image, ImageDraw, ImageFont
from io import BytesIO
import base64
import threading
import pywhatkit as kit
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.image import MIMEImage
from dotenv import load_dotenv
import pandas as pd

load_dotenv()

app = Flask(__name__)

# Directorio para guardar las imágenes
image_dir = "assets/images"
os.makedirs(image_dir, exist_ok=True)

# Variables globales para la cámara y los hilos
cap = None
output_frame = None
lock = threading.Lock()

# Variables para la imagen generada 1
generated_image_bytes_1 = None
generated_image_path_1 = os.path.join(image_dir, "generated_1.png")
# Variables para la imagen generada 2
generated_image_bytes_2 = None
generated_image_path_2 = os.path.join(image_dir, "generated_2.png")
# Variables para la imagen combinada
combined_image_path = os.path.join(image_dir, "combined_image.png")

# Rutas de los marcos
marco_path = os.path.join(image_dir, "marco.png")

# Archivo de Excel
EXCEL_FILE_PATH = "registros_estudiantes.xlsx"

EMAIL_CONFIG = {
    'sender': 'proyectofotoia@gmail.com',  # Tu dirección de email
    'password': os.getenv("PASSWORD_EMAIL"),  # Tu contraseña o app password
    'smtp_server': 'smtp.gmail.com',  # Servidor SMTP (para Gmail)
    'port': 587  # Puerto para TLS
}

# Diccionario de abreviaturas de profesiones
ABBREVIATIONS = {
    "administracion de empresas": "Lic",
    "antropologia": "Lic",
    "arquitectura": "Arq",
    "biomedicina": "Ing",
    "bioquimica y farmacia": "Bioq.F",
    "biotecnologia": "Ing",
    "ciencias de datos": "Ing",
    "ciencias politicas": "Lic",
    "comercio exterior": "Lic",
    "comunicacion": "Lic",
    "computacion": "Ing",
    "contabilidad y auditoria": "Lic",
    "derecho": "Abg",
    "diseno multimedia": "Lic",
    "economia": "Lic",
    "educacion basica": "Lic",
    "educacion inicial": "Lic",
    "educacion intercultural bilingue": "Lic",
    "electronica y automatizacion": "Ing",
    "electricidad": "Ing",
    "enfermeria": "Lic",
    "finanzas": "Lic",
    "fisioterapia": "Lic",
    "gestion ambiental": "Lic",
    "ingenieria automotriz": "Ing",
    "ingenieria civil": "Ing",
    "ingenieria industrial": "Ing",
    "marketing e inteligencia de mercados": "Lic",
    "mecatronica": "Ing",
    "negocios digitales": "Lic",
    "odontologia": "Od",
    "pedagogia de la actividad fisica y deporte": "Lic",
    "psicologia": "Lic",
    "psicologia clinica": "Psic. clín",
    "software": "Ing",
    "teologia": "Lic"
}


def get_camera_feed():
    """Genera el feed de la cámara para la interfaz web."""
    global cap
    if cap is None or not cap.isOpened():
        cap = cv2.VideoCapture(1)

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


def generate_image_process(original_path, profession, image_number):
    """
    Función que ejecuta el proceso de generación de imagen de Gemini en un hilo.
    """
    global generated_image_bytes_1, generated_image_bytes_2
    print(f"Enviando foto a Gemini para la imagen {image_number}...")

    # Llama a la función de Gemini, que ahora seleccionará un prompt al azar
    new_image_bytes = generate_image_with_gemini(original_path, profession)

    if image_number == 1:
        generated_image_bytes_1 = new_image_bytes
    else:
        generated_image_bytes_2 = new_image_bytes
    print(f"Imagen {image_number} generada.")


def superponer_marco_texto(imagen_generada_bytes, ruta_marco, nombre_est, profesion):
    """
    Superpone un marco y agrega el texto con la abreviatura y el nombre a la imagen generada.
    """
    try:
        # Cargar la imagen generada y el marco
        img_generada = Image.open(BytesIO(imagen_generada_bytes))
        img_marco = Image.open(ruta_marco)

        # Redimensionar el marco para que coincida con la imagen generada
        img_marco = img_marco.resize(img_generada.size, Image.LANCZOS)

        # Superponer el marco (asumiendo que el marco tiene transparencia)
        img_generada.paste(img_marco, (0, 0), img_marco)

        # Agrega el texto
        draw = ImageDraw.Draw(img_generada)

        # Obtener la abreviatura de la profesion
        abreviatura_profesion = ABBREVIATIONS.get(profesion, profesion.upper())

        # Crear el texto para el nombre
        texto_nombre = f"{abreviatura_profesion}. {nombre_est}"
        texto_profesion = profesion.upper()  # Mostrar la profesión en mayúsculas

        # Definir la fuente y el tamaño (ajustar según el diseño)
        try:
            font_nombre = ImageFont.truetype("arial.ttf", 45)
            font_profesion = ImageFont.truetype("arial.ttf", 30)  # Una fuente un poco más pequeña para la profesión
        except IOError:
            font_nombre = ImageFont.load_default()
            font_profesion = ImageFont.load_default()
            print("Fuente 'arial.ttf' no encontrada, usando la fuente por defecto.")

        # Calcular el tamaño del texto del nombre para centrarlo
        bbox_nombre = draw.textbbox((0, 0), texto_nombre, font=font_nombre)
        text_width_nombre = bbox_nombre[2] - bbox_nombre[0]
        text_height_nombre = bbox_nombre[3] - bbox_nombre[1]

        # Coordenadas para centrar el nombre en la parte inferior
        image_width, image_height = img_generada.size
        x_pos_nombre = (image_width - text_width_nombre) / 2
        y_pos_nombre = image_height - text_height_nombre - 130

        # Dibujar el texto del nombre
        draw.text(
            (x_pos_nombre, y_pos_nombre),
            texto_nombre,
            font=font_nombre,
            fill=(255, 165, 0),
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

        # Calcular el tamaño del texto de la profesión para centrarlo
        bbox_profesion = draw.textbbox((0, 0), texto_profesion, font=font_profesion)
        text_width_profesion = bbox_profesion[2] - bbox_profesion[0]
        text_height_profesion = bbox_profesion[3] - bbox_profesion[1]

        # Coordenadas para centrar la profesión debajo del nombre
        x_pos_profesion = (image_width - text_width_profesion) / 2
        y_pos_profesion = y_pos_nombre + text_height_nombre + 10  # Ajustar el espacio entre los textos

        # Dibujar el texto de la profesión
        draw.text(
            (x_pos_profesion, y_pos_profesion),
            texto_profesion,
            font=font_profesion,
            fill=(255, 165, 0),
            stroke_width=2,
            stroke_fill=(0, 0, 0)
        )

        # Guardar la imagen final en un buffer para ser usada
        buffer = BytesIO()
        img_generada.save(buffer, format="PNG")
        buffer.seek(0)
        return buffer.getvalue()
    except FileNotFoundError:
        print(f"Error: No se encontró el archivo del marco en {ruta_marco}")
        return None
    except Exception as e:
        print(f"Error al superponer el marco: {e}")
        return None


def combinar_imagenes_horizontalmente(image_path_1, image_path_2):
    """
    Combina dos imágenes horizontalmente sin añadir texto.
    """
    try:
        img1 = Image.open(image_path_1)
        img2 = Image.open(image_path_2)

        # Se redimensionan para que tengan la misma altura si fuera necesario
        min_height = min(img1.height, img2.height)
        img1 = img1.resize((int(img1.width * min_height / img1.height), min_height), Image.LANCZOS)
        img2 = img2.resize((int(img2.width * min_height / img2.height), min_height), Image.LANCZOS)

        # Crear una nueva imagen con el ancho de ambas y la altura mínima
        combined_image = Image.new('RGB', (img1.width + img2.width + 20, min_height), (255, 255, 255))
        
        # Pegar las imágenes en la nueva imagen
        combined_image.paste(img1, (0, 0))
        combined_image.paste(img2, (img1.width + 20, 0))

        # Guardar la imagen combinada
        combined_image.save(combined_image_path)
        print(f"Imagen combinada guardada en {combined_image_path}")
        return combined_image_path

    except Exception as e:
        print(f"Error al combinar las imágenes: {e}")
        return None


# Guardar datos en Excel
def save_student_data(data):
    """Guarda los datos del estudiante en un archivo de Excel."""
    try:
        df = pd.DataFrame([data])

        if os.path.exists(EXCEL_FILE_PATH):
            # Si el archivo existe, leemos los datos existentes y concatenamos
            existing_df = pd.read_excel(EXCEL_FILE_PATH)
            updated_df = pd.concat([existing_df, df], ignore_index=True)
            updated_df.to_excel(EXCEL_FILE_PATH, index=False)
            print(f"Datos de {data['nombre']} agregados al archivo de Excel.")
        else:
            # Si no existe, creamos uno nuevo
            df.to_excel(EXCEL_FILE_PATH, index=False)
            print("Archivo de Excel creado con los primeros datos.")
    except Exception as e:
        print(f"Error al guardar los datos en Excel: {e}")


@app.route('/')
def index():
    """Ruta principal que muestra la interfaz web con el formulario."""
    return render_template_string("""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Transformación Profesional Instantánea</title>
            <style>
                body { font-family: Arial, sans-serif; text-align: center; margin: 0px; background-color: #FFFFFF; }
                header { display: flex; align-items: center; justify-content: space-between; background-color: #00B2EE; padding: 20px; color: white; border: 5px solid #000000; }
                #header-logo { width: -20%; height: 50px; margin-left: 20px; }
                .header-title { flex-grow: 1; text-align: center; }
                
                .main-content { 
                    display: flex; 
                    justify-content: center; 
                    align-items: flex-start; 
                    gap: 10px; 
                    margin-top: 100px; 
                }

                .image-box { 
                    border: 10px solid #000000; 
                    padding: 10px; 
                    width: 330px; /* Ajuste el ancho para 3 imágenes */
                    height: 540px; 
                    background-color: #304870; 
                    color: white; 
                }
                #original_image { border: 5px solid #F5EF2C; width: 98%; height: -88%; object-fit: contain; }
                #generated_image_1 { border: 5px solid #F5EF2C; width: 98%; height: -88%; object-fit: contain; }
                #generated_image_2 { border: 5px solid #F5EF2C; width: 98%; height: -88%; object-fit: contain; }
                                                     
                .form-container { 
                    width: 300px; 
                    padding: 20px; 
                    border: 5px solid #00B2EE; 
                    border-radius: 10px; 
                    text-align: left; 
                    background-color: #f0f0f0; 
                }
                
                .form-container button{
                    height: 40px; 
                    width: 100%;  
                    margin-bottom: 15px;
                }
                                                     
                .form-container label, .form-container input, .form-container select { 
                    display: block; 
                    width: 100%; 
                    margin-bottom: 10px; 
                }
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
            
            <div class="main-content">
                <div class="form-container">
                    <h2>Datos del Estudiante</h2>
                    <form id="data-form">
                        <label for="nombre">Nombre Y Apellido del estudiante:</label>
                        <input type="text" id="nombre" name="nombre" required>
                        <label for="profesion">Profesión:</label>
                        <select id="profesion" name="profesion" required>
                            <option value="">Seleccione una profesión</option>
                            <option value="administracion de empresas">Administracion de Empresas</option>
                            <option value="antropologia">Antropología</option>
                            <option value="arquitectura">Arquitectura</option>
                            <option value="biomedicina">Biomedicina</option>
                            <option value="bioquimica y farmacia">Bioquimica y Farmacia</option>
                            <option value="biotecnologia">Biotecnologia</option>
                            <option value="ciencias de datos">Ciencias de Datos</option>
                            <option value="ciencias politicas">Ciencias Políticas</option>
                            <option value="comercio exterior">Comercio Exterior</option>
                            <option value="comunicacion">Comunicación</option>
                            <option value="computacion">Computacion</option>
                            <option value="contabilidad y auditoria">Contabilidad y Auditoria</option>
                            <option value="derecho">Derecho</option>
                            <option value="diseno multimedia">Diseño Multimedia</option>
                            <option value="economia">Economia</option>
                            <option value="educacion basica">Educación Básica</option>
                            <option value="educacion inicial">Educacion Inicial</option>
                            <option value="educacion intercultural bilingue">Eduación Intercultural Bilingüe</option>
                            <option value="electronica y automatizacion">Electronica y Automatizacion</option>
                            <option value="electricidad">Electricidad</option>
                            <option value="enfermeria">Enfermeria</option>
                            <option value="finanzas">Finanzas</option>
                            <option value="fisioterapia">Fisioterapia</option>
                            <option value="gestion ambiental">Gestión Ambiental</option>
                            <option value="ingenieria automotriz">Ingenieria Automotriz</option>
                            <option value="ingenieria civil">Ingenieria Civil</option>
                            <option value="ingenieria industrial">Ingenieria Industrial</option>
                            <option value="marketing e inteligencia de mercados">Marketing e Inteligencia de Mercados</option>
                            <option value="mecatronica">Mecatronica</option>
                            <option value="negocios digitales">Negocios Digitales</option>
                            <option value="odontologia">Odontologia</option>
                            <option value="pedagogia de la actividad fisica y deporte">Pedagogia de la Actividad Fisica y Deporte</option>
                            <option value="psicologia">Psicologia</option>
                            <option value="psicologia clinica">Psicologia Clinica</option>
                            <option value="software">Software</option>
                            <option value="teologia">Teología</option>
                        </select>
                        <label for="email">Correo Electrónico:</label>
                        <input type="email" id="email" name="email" required>
                        <label for="whatsapp">Número de WhatsApp:</label>
                        <input type="tel" id="whatsapp" name="whatsapp" required>
                        <button type="button" onclick="captureAndGenerate()">Capturar y Generar</button>
                        <button type="button" onclick="clearImages()">Limpiar</button>
                        <button type="button" onclick="sendToWhatsapp()">Enviar Whatsapp</button>
                        <button type="button" onclick="sendToEmail()">Enviar Email</button>
                    </form>
                </div>
                                                     
                <div class="image-box">
                    <h2>En Vivo</h2>
                    <img id="original_image" src="{{ url_for('video_feed') }}">
                </div>

                <div class="image-box">
                    <h2>Imagen Generada 1</h2>
                    <img id="generated_image_1" src="">
                </div>
                
                <div class="image-box">
                    <h2>Imagen Generada 2</h2>
                    <img id="generated_image_2" src="">
                </div>
            </div>

            <script>
                function captureAndGenerate() {
                    const form = document.getElementById('data-form');
                    const formData = new FormData(form);
                    const profesion = formData.get('profesion');

                    if (profesion === "") {
                        alert("Por favor, selecciona una profesión.");
                        return;
                    }

                    fetch('/capture', { 
                        method: 'POST',
                        body: JSON.stringify({
                            nombre: formData.get('nombre'),
                            profesion: profesion,
                            email: formData.get('email'),
                            whatsapp: formData.get('whatsapp')
                        }),
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        if (data.status === 'success') {
                            document.getElementById('generated_image_1').src = data.generated_image_url_1;
                            document.getElementById('generated_image_2').src = data.generated_image_url_2;
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
                                document.getElementById('generated_image_1').src = "";
                                document.getElementById('generated_image_2').src = "";
                            }
                        });
                }
                                                     
                function sendToEmail(){
                    const form = document.getElementById('data-form');
                    const formData = new FormData(form);
                    const email_address = formData.get('email')
                    const whatsapp_number = formData.get('whatsapp');
                                                                                     
                    if (document.getElementById('generated_image_1').src === "" || document.getElementById('generated_image_2').src === "") {
                        alert("Primero debes generar las imágenes.");
                        return;
                    }
                                                                                     
                    fetch('/send_to_email', {
                        method: 'POST',
                        body: JSON.stringify({
                            email: email_address,
                            nombre: formData.get('nombre'),
                            whatsapp: whatsapp_number,
                            profesion: formData.get('profesion')
                        }),
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Ocurrió un error al enviar el email.');
                    });
                                                                                     
                }

                function sendToWhatsapp() {
                    const form = document.getElementById('data-form');
                    const formData = new FormData(form);
                    const whatsapp_number = formData.get('whatsapp');
                    const profesion = formData.get('profesion');
                    const email_address = formData.get('email');

                    if (!whatsapp_number) {
                        alert("Por favor, ingresa un número de WhatsApp.");
                        return;
                    }

                    if (document.getElementById('generated_image_1').src === "" || document.getElementById('generated_image_2').src === "") {
                        alert("Primero debes generar las imágenes.");
                        return;
                    }
                    
                    fetch('/send_to_whatsapp', {
                        method: 'POST',
                        body: JSON.stringify({
                            whatsapp: whatsapp_number,
                            nombre: formData.get('nombre'),
                            profesion: profesion,
                            email: email_address
                        }),
                        headers: {
                            'Content-Type': 'application/json'
                        }
                    })
                    .then(response => response.json())
                    .then(data => {
                        alert(data.message);
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        alert('Ocurrió un error al enviar el mensaje de WhatsApp.');
                    });
                }
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
    Ruta que captura la foto de la cámara, la procesa con Gemini,
    le añade un marco y devuelve la imagen final.
    """
    global cap, generated_image_bytes_1, generated_image_bytes_2, generated_image_path_1, generated_image_path_2, marco_path

    if cap is None or not cap.isOpened():
        return jsonify({"status": "error", "message": "No se pudo acceder a la cámara."})

    data = request.get_json()
    profession = data.get('profesion')
    nombre_est = data.get('nombre')

    if not profession:
        return jsonify({"status": "error", "message": "No se seleccionó ninguna profesión."})

    ret, frame = cap.read()
    if not ret:
        return jsonify({"status": "error", "message": "No se pudo capturar el frame."})

    original_path = os.path.join(image_dir, "original.png")
    cv2.imwrite(original_path, frame)
    print(f"Foto original guardada en {original_path}")

    # Iniciar la generación de ambas imágenes en hilos separados para mayor rapidez
    gemini_thread_1 = threading.Thread(target=generate_image_process, args=(original_path, profession, 1))
    gemini_thread_2 = threading.Thread(target=generate_image_process, args=(original_path, profession, 2))

    gemini_thread_1.start()
    gemini_thread_2.start()

    gemini_thread_1.join()
    gemini_thread_2.join()

    # Procesar la primera imagen
    if generated_image_bytes_1:
        final_image_bytes_1 = superponer_marco_texto(
            generated_image_bytes_1.data,
            marco_path,
            nombre_est,
            profession
        )
        if final_image_bytes_1:
            with open(generated_image_path_1, 'wb') as f:
                f.write(final_image_bytes_1)
            encoded_image_1 = base64.b64encode(final_image_bytes_1).decode('utf-8')
            image_data_uri_1 = f"data:image/png;base64,{encoded_image_1}"
        else:
            return jsonify({"status": "error", "message": "Error al superponer el marco en la primera imagen."})
    else:
        return jsonify({"status": "error", "message": "No se pudo generar la primera imagen con Gemini."})

    # Procesar la segunda imagen
    if generated_image_bytes_2:
        final_image_bytes_2 = superponer_marco_texto(
            generated_image_bytes_2.data,
            marco_path,
            nombre_est,
            profession
        )
        if final_image_bytes_2:
            with open(generated_image_path_2, 'wb') as f:
                f.write(final_image_bytes_2)
            encoded_image_2 = base64.b64encode(final_image_bytes_2).decode('utf-8')
            image_data_uri_2 = f"data:image/png;base64,{encoded_image_2}"
        else:
            return jsonify({"status": "error", "message": "Error al superponer el marco en la segunda imagen."})
    else:
        return jsonify({"status": "error", "message": "No se pudo generar la segunda imagen con Gemini."})

    return jsonify({
        "status": "success",
        "generated_image_url_1": image_data_uri_1,
        "generated_image_url_2": image_data_uri_2
    })


@app.route('/send_to_email', methods=['POST'])
def send_to_email():
    """Ruta para enviar la imagen generada al email del estudiante."""
    global generated_image_path_1, generated_image_path_2
    data = request.get_json()
    email = data.get('email')
    nombre = data.get('nombre')
    profesion = data.get('profesion')
    whatsapp_number = data.get('whatsapp')  # <-- Añadido para capturar el número de WhatsApp

    # Registramos los datos en el Excel
    student_data = {'nombre': nombre, 'profesion': profesion, 'email': email, 'whatsapp': whatsapp_number}
    save_student_data(student_data)

    if not os.path.exists(generated_image_path_1) or not os.path.exists(generated_image_path_2):
        return jsonify({"status": "error", "message": "No hay imágenes generadas para enviar."})

    try:
        # Crear el mensaje
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender"]
        msg['To'] = email
        msg['Subject'] = f"Tu transformación profesional como {profesion}"

        # Cuerpo del mensaje
        body = f"""
        <html>
            <body>
                <h2>Hola {nombre},</h2>
                <p>Aquí tienes tus dos imágenes transformadas con la profesión de {profesion}.</p>
                <p>¡Esperamos que te gusten!</p>
                <img src="cid:image1" width="400">
                <img src="cid:image2" width="400">
                <p>Saludos,<br>El equipo de Transformación Profesional</p>
            </body>
        </html>
        """
        msg.attach(MIMEText(body, 'html'))

        # Adjuntar la imagen 1
        with open(generated_image_path_1, 'rb') as img_file:
            img1 = MIMEImage(img_file.read())
            img1.add_header('Content-ID', '<image1>')
            msg.attach(img1)

        # Adjuntar la imagen 2
        with open(generated_image_path_2, 'rb') as img_file:
            img2 = MIMEImage(img_file.read())
            img2.add_header('Content-ID', '<image2>')
            msg.attach(img2)

        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender"], EMAIL_CONFIG["password"])
            server.send_message(msg)

        return jsonify({"status": "success", "message": f"Email enviado exitosamente a {email}."})

    except Exception as e:
        print(f"Error al enviar el email: {e}")
        return jsonify({"status": "error", "message": f"Error al enviar el email. Error: {str(e)}"})


@app.route('/send_to_whatsapp', methods=['POST'])
def send_to_whatsapp():
    """Ruta para enviar la imagen generada al WhatsApp del estudiante."""
    global generated_image_path_1, generated_image_path_2, combined_image_path
    data = request.get_json()
    whatsapp_number = data.get('whatsapp')
    nombre = data.get('nombre')
    profesion = data.get('profesion')
    email = data.get('email')

    # Registramos los datos en el Excel
    student_data = {'nombre': nombre, 'profesion': profesion, 'email': email, 'whatsapp': whatsapp_number}
    save_student_data(student_data)

    if not whatsapp_number:
        return jsonify({"status": "error", "message": "Número de WhatsApp no proporcionado."})

    if not os.path.exists(generated_image_path_1) or not os.path.exists(generated_image_path_2):
        return jsonify({"status": "error", "message": "No hay imágenes generadas para enviar."})
    
    # Combinar las dos imágenes en una sola
    combined_image_path = combinar_imagenes_horizontalmente(generated_image_path_1, generated_image_path_2)

    if not combined_image_path:
        return jsonify({"status": "error", "message": "Error al combinar las imágenes."})
    
    message = f"Hola {nombre}, aquí están tus dos imágenes generadas con la profesión de {profesion}. ¡Esperamos que te gusten!"
    
    try:
        print(f"Enviando imagen combinada a {whatsapp_number}...")
        # Ahora solo se envía una imagen combinada
        kit.sendwhats_image(whatsapp_number, combined_image_path, caption=message)

        return jsonify({"status": "success", "message": f"Imágenes combinadas y texto enviados a WhatsApp exitosamente a {whatsapp_number}."})
    except Exception as e:
        print(f"Error al enviar la imagen a WhatsApp: {e}")
        return jsonify({"status": "error", "message": f"Error al enviar la imagen a WhatsApp. Asegúrate de que el número sea válido y WhatsApp Web esté abierto. Error: {e}"})


@app.route('/clear', methods=['POST'])
def clear_images():
    """Ruta para limpiar las imágenes generadas."""
    global generated_image_bytes_1, generated_image_bytes_2
    generated_image_bytes_1 = None
    generated_image_bytes_2 = None
    try:
        if os.path.exists(generated_image_path_1):
            os.remove(generated_image_path_1)
        if os.path.exists(generated_image_path_2):
            os.remove(generated_image_path_2)
        if os.path.exists(combined_image_path):
            os.remove(combined_image_path)
        print("Imágenes generadas eliminadas.")
    except FileNotFoundError:
        pass
    return jsonify({"status": "success"})


if __name__ == '__main__':
    host_ip = '0.0.0.0'
    port_number = 5000

    print("--------------------------------------------------")
    print(f"La aplicación Flask está corriendo en http://127.0.0.1:{port_number}")
    print("Haz clic en el enlace de arriba para abrir la aplicación en tu navegador.")
    print("--------------------------------------------------")

    try:
        app.run(host=host_ip, port=port_number, debug=False)
    finally:
        if cap is not None:
            cap.release()