import cv2
import os
from core.gemini_process import generate_image_with_gemini
from PIL import Image
from io import BytesIO
import base64

def main():
    """
    Función principal de la aplicación.
    """
    #print("--- Transformación Profesional Instantánea ---")
    #print("Presiona 'c' para tomar una foto, 'q' para salir.")
    
    # 1. Configurar la webcam
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("Error: No se pudo acceder a la cámara.")
        return

    # 2. Bucle principal para mostrar la cámara
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        # Muestra el feed de la cámara
        cv2.imshow('Webcam - Presiona "c" para capturar', frame)
        
        key = cv2.waitKey(1)
        
        # Capturar foto
        if key == ord('c'):
            #profession = input("Ingresa la profesión (ej: astronauta, chef, médico): ")
            
            # Guardar la foto original
            original_path = "assets/images/original.png"
            os.makedirs("assets/images", exist_ok=True)
            cv2.imwrite(original_path, frame)
            print(f"Foto original guardada en {original_path}")
            
            print("Enviando foto a Gemini... Esto puede tomar unos segundos.")
            
            # 3. Llamar al procesador de Gemini
            generated_image_bytes = generate_image_with_gemini(original_path)
            
            if generated_image_bytes:
                # 4. Guardar y mostrar la imagen generada
                generated_image_path = "assets/images/generated.png"
                
                
                # Convierte los bytes en una imagen de PIL y la guarda
                generated_image_pil = Image.open(BytesIO(generated_image_bytes.data))
                generated_image_pil.save(generated_image_path)
                
                print(f"Imagen generada guardada en {generated_image_path}")
                
                # Muestra la imagen generada con OpenCV
                img_generated = cv2.imread(generated_image_path)
                if img_generated is not None:
                    cv2.imshow('Imagen Generada', img_generated)
                print("¡Listo! La foto generada se está mostrando en una nueva ventana.")
                break
            else:
                print("No se pudo generar la imagen.")
            
        # Salir de la aplicación
        if key == ord('q'):
            break

    # Liberar recursos
    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    main()