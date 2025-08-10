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
        "policia": [
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un policía, en una calle de la ciudad con un coche patrulla de fondo. Mantén el fotorrealismo, la misma pose, expresión facial e género",
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un policía, en una comisaría con otros agentes de fondo. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un policía, posando en la entrada de un edificio del gobierno. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "bombero": [
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un bombero, sosteniendo un casco, en un fondo de una estación de bomberos. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un bombero, con una manguera de fondo y un camión de bomberos en la distancia. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un bombero, de pie frente a un edificio en llamas (de manera segura y controlada). Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "medico": [
            "transforma a la persona en esta foto para que esté vestido con una bata de médico, en una sala de hospital moderna. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un cirujano, en un quirófano. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con ropa de médico, en un consultorio con instrumental médico. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "astronauta": [
            "transforma a la persona en esta foto para que esté vestido con un traje de astronauta, flotando en el espacio con la Tierra de fondo. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con un traje de astronauta, dentro de la Estación Espacial Internacional. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con un traje de astronauta, de pie en la superficie de la luna con un cielo estrellado. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "electricista": [
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un electricista, trabajando con un panel eléctrico en un taller. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido como electricista, con un casco y herramientas, en una obra de construcción. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un electricista, de pie junto a un transformador de energía en un ambiente industrial. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "abogado": [
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un abogado, en una sala de corte con estanterías de libros legales. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con un traje formal de abogado, en un despacho de abogados con una vista de la ciudad. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido como un abogado, de pie en la entrada de un tribunal. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "chef": [
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un chef, en una cocina de restaurante de alta gama. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un chef, sosteniendo un plato, en un ambiente de cocina moderna. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un chef, de pie en una pastelería con postres en exhibición. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "arquitecto": [
            "transforma a la persona en esta foto para que esté vestido como un arquitecto, de pie en un estudio con planos y maquetas de edificios. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido como un arquitecto, visitando una obra en construcción con un casco. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido como un arquitecto, con un ordenador y software de diseño de fondo. Mantén el fotorrealismo, la misma pose, expresión facial e género."
        ],
        "programador": [
            "transforma a la persona en esta foto para que esté vestido con el uniforme de un programador, en una oficina de tecnología con varios monitores. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con ropa de programador, de pie frente a una pizarra con código. Mantén el fotorrealismo, la misma pose, expresión facial e género.",
            "transforma a la persona en esta foto para que esté vestido con un suéter con capucha, programando en una cafetería. Mantén el fotorrealismo, la misma pose, expresión facial e género."
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