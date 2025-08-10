# geminis_process.py
from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
import random  # Importamos el módulo random
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("No se encontró la clave API de Gemini. Asegúrate de que el archivo .env exista y contenga GOOGLE_API_KEY.")


# Función auxiliar para generar el prompt dinámico
def create_dynamic_prompt(profession):
    """
    Genera un prompt descriptivo basado en la profesión seleccionada, eligiendo uno al azar.
    """
    # Diccionario con listas de prompts para cada profesión
    profession_prompts = {
        "administracion de empresas": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un administrador de empresas, en una sala de reuniones. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un administrador de empresas, en una oficina moderna con un ordenador. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un administrador de empresas, de pie frente a una pizarra de finanzas. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "arquitectura": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un arquitecto, en un estudio de diseño con planos. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un arquitecto, visitando una obra de construcción con un casco. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un arquitecto, presentando una maqueta de un edificio. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "biomedicina": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un biomédico, en un laboratorio con microscopios. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un biomédico, analizando muestras médicas en un ambiente estéril. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un biomédico, de pie en un laboratorio de investigación. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "bioquimica y farmacia": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un bioquímico, manipulando químicos en un laboratorio. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un farmacéutico, atendiendo a un cliente en una farmacia. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un bioquímico, examinando medicamentos en un laboratorio. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "biotecnologia": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un biotecnólogo, en un laboratorio de genética con equipos avanzados. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un biotecnólogo, observando células en un microscopio. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un biotecnólogo, de pie en un invernadero de alta tecnología. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "computacion": [
            "transforma a la persona en esta foto para que esté vestida con ropa de programador, en una oficina de tecnología con múltiples monitores. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con ropa casual, de pie frente a una pizarra con código de programación. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con ropa casual, trabajando en una computadora en una cafetería. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "contabilidad y auditoria": [
            "transforma a la persona en esta foto para que esté vestida con un traje formal, de pie en una oficina con libros contables. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un contador, revisando documentos financieros. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con un traje formal, de pie en una sala de juntas. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "economia": [
            "transforma a la persona en esta foto para que esté vestida con un traje formal de economista, en una sala de reuniones. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con un traje formal de economista, analizando gráficos de mercado. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con un traje formal de economista, dando una conferencia en un auditorio. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "derecho": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un abogado, en una sala de corte con estanterías de libros legales. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con un traje formal de abogado, en un despacho de abogados con una vista de la ciudad. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida como un abogado, de pie en la entrada de un tribunal. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "diseno multimedia": [
            "transforma a la persona en esta foto para que esté vestida con ropa casual de diseñador, en un estudio de diseño con un ordenador. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con ropa casual, de pie frente a una pantalla con un diseño gráfico. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con ropa de diseñador, trabajando en una tableta gráfica. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "educacion inicial": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un profesor de educación inicial, en un aula de preescolar. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un profesor de educación inicial, leyendo un libro a un grupo de niños. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un profesor de educación inicial, en un patio de juegos con niños. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "electronica y automatizacion": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero en electrónica, en un laboratorio con placas de circuitos. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero en electrónica, de pie junto a una maquinaria automatizada. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero en electrónica, manipulando un robot industrial. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "electricidad": [
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un electricista, trabajando con un panel eléctrico en un taller. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido como electricista, con un casco y herramientas, en una obra de construcción. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un electricista, de pie junto a un transformador de energía en un ambiente industrial. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "enfermeria": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de una enfermera, en una sala de hospital. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de una enfermera, atendiendo a un paciente en una camilla. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de una enfermera, en una clínica de salud. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "fisioterapia": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un fisioterapeuta, en una clínica con equipos de rehabilitación. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un fisioterapeuta, ayudando a un paciente a hacer ejercicio. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un fisioterapeuta, en una sesión de rehabilitación. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "ingenieria automotriz": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero automotriz, trabajando en el motor de un coche. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero automotriz, diseñando un vehículo en un ordenador. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero automotriz, en una fábrica de coches. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "ingenieria civil": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero civil, en una obra de construcción con un casco. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero civil, revisando planos de un edificio. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero civil, de pie en un puente. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "ingenieria industrial": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero industrial, en una línea de producción optimizada. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero industrial, de pie en una fábrica con robots. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero industrial, analizando un proceso de fabricación. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "mecatronica": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero mecatrónico, de pie en un taller de robótica. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero mecatrónico, ensamblando un robot. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un ingeniero mecatrónico, trabajando en una interfaz humano-robot. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "negocios digitales": [
            "transforma a la persona en esta foto para que esté vestida con ropa casual de negocios, en una oficina de marketing digital con gráficos. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con ropa casual de negocios, de pie frente a una pizarra con estrategias digitales. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con ropa casual de negocios, en un espacio de coworking. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "odontologia": [
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un odontólogo, en un consultorio dental. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un odontólogo, con un paciente en la silla. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con el uniforme de un odontólogo, sosteniendo herramientas dentales. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "pedagogia de la actividad fisica y deporte": [
            "transforma a la persona en esta foto para que esté vestida con ropa deportiva, en una cancha de baloncesto con estudiantes. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con ropa deportiva, en un gimnasio con equipos de entrenamiento. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida con ropa deportiva, enseñando a un grupo de niños a jugar al fútbol. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "psicologia": [
            "transforma a la persona en esta foto para que esté vestida como un psicólogo, en un consultorio con un diván. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida como un psicólogo, de pie en una sala de terapia grupal. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida como un psicólogo, escribiendo notas en un portapapeles. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "psicologia clinica": [
            "transforma a la persona en esta foto para que esté vestida como un psicólogo clínico, en un consultorio con un diván. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida como un psicólogo clínico, de pie en un hospital con un portapapeles. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestida como un psicólogo clínico, en una sesión de terapia. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
    }
    
    # Obtenemos la lista de prompts para la profesión o una lista por defecto si no existe
    prompts_list = profession_prompts.get(profession.lower(), ["vestido con la ropa de un profesional, en un entorno de oficina."])
    
    # Seleccionamos un prompt al azar de la lista
    selected_prompt = random.choice(prompts_list)

    # El prompt final ahora se crea de forma más concisa
    final_prompt = f"Eres un artista digital experto. {selected_prompt} El resultado debe ser solo la imagen."

    return final_prompt

def generate_image_with_gemini(image_path, profession):
    """
    Toma una imagen y una profesión, y genera una nueva imagen con Gemini.

    Args:
        image_path (str): Ruta de la imagen original.
        profession (str): La profesión que se usará en el prompt.

    Returns:
        bytes: Los bytes de la imagen generada.
    """
    try:
        # Abre la imagen original
        img = Image.open(image_path)

        # Configura el cliente de la API de Gemini
        client = genai.Client(api_key=API_KEY)

        # Genera el prompt dinámicamente con la profesión
        prompt = create_dynamic_prompt(profession)
        
        print(f"Prompt enviado a Gemini: {prompt}")

        # Llama a la API de Gemini con el prompt y la imagen
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=[prompt, img],
            config=types.GenerateContentConfig(response_modalities=['TEXT', 'IMAGE'])
        )

        if response is not None:
            print("Geminis generó imagen")

        generate_image_data = None
        # Busca la imagen generada en la respuesta de la API
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                print("Se encontró la imagen.")
                generate_image_data = part.inline_data
                break
            elif part.text is not None:
                print(f"Texto en la respuesta: {part.text}")
        
        if generate_image_data:
            return generate_image_data
        else:
            print("Error: No se encontró una imagen válida en la respuesta de Gemini.")
            return None

    except Exception as e:
        print(f"Ocurrió un error al llamar a la API de Gemini: {e}")
        return None