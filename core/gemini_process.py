from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO
import os
from dotenv import load_dotenv

load_dotenv()
API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    raise ValueError("No se encontró la clave API de Gemini. Asegúrate de que el archivo .env exista y contenga GOOGLE_API_KEY.")


# Configura la API
#genai.configure(api_key=API_KEY)
#model = genai.GenerativeModel('gemini-2.0-flash-preview-image-generation')

def generate_image_with_gemini(image_path):
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

        client = genai.Client(api_key=API_KEY)

        # Crea un prompt descriptivo para obtener mejores resultados
        prompt = (
            "Eres un artista digital experto. Transforma a la persona en esta foto para que ",
            "esté vestida con el uniforme de un chef. Mantén el fotorrealismo, ",
            "la misma pose, expresión facial e iluminación. El resultado debe ser solo la imagen."
        )

        # Llama a la API de Gemini con el prompt y la imagen
        response = client.models.generate_content(
            model="gemini-2.0-flash-preview-image-generation",
            contents=[prompt, img],
            config=types.GenerateContentConfig(response_modalities=['TEXT', 'IMAGE'])
        )

        if response is not None:
            print("Geminis genero imagen")

        generate_image_data = None
        # Busca la imagen generada en la respuesta de la API
        for part in response.candidates[0].content.parts:
            if part.inline_data is not None:
                print("Se encontro la imagen.")
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