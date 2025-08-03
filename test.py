from google import genai
from google.genai import types
from PIL import Image
from io import BytesIO

import PIL.Image

image = PIL.Image.open(r"C:\Users\PC\Desktop\proyecto_foto\assets\images\original.png")

client = genai.Client(api_key="AIzaSyC-2lBbjcMCApnjx4Z5cnMv_PuGPqewqgc")

text_input = ("Transforma a la persona en esta imagen para que esté vestida como un ingeniera industrial.")

response = client.models.generate_content(
    model="gemini-2.0-flash-preview-image-generation",
    contents=[text_input, image],
    config=types.GenerateContentConfig(
      response_modalities=['TEXT', 'IMAGE']
    )
)

for part in response.candidates[0].content.parts:
  if part.text is not None:
    print(part.text)
  elif part.inline_data is not None:
    image = Image.open(BytesIO((part.inline_data.data)))
    image.show()