
import os
from google import genai

def main():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Falta configurar GEMINI_API_KEY")

    print("GTA VIRAL FACTORY")
    print("Conectando con Gemini...")

    client = genai.Client(api_key=api_key)

    prompt = """
    Actúa como guionista profesional de YouTube Shorts y TikTok.
    Crea un guion ORIGINAL en español de España sobre GTA 6.

    Requisitos:
    - Duración aproximada: 30 segundos.
    - Empieza con una frase que enganche en los primeros 2 segundos.
    - Tema: 3 detalles interesantes de GTA 6.
    - No inventes filtraciones ni presentes rumores como hechos.
    - Si algo es especulación, indícalo claramente.
    - Termina con una pregunta para generar comentarios.

    Devuelve:
    1. Título llamativo.
    2. Narración completa.
    3. Ideas de imágenes o escenas para acompañarla.
    4. Descripción y hashtags.
    """

    response = client.models.generate_content(
       model="gemini-3.5-flash-lite",
        contents=prompt
    )

    guion = response.text

    if not guion:
        raise RuntimeError("Gemini no ha devuelto texto.")

    with open("guion_gta6.txt", "w", encoding="utf-8") as archivo:
        archivo.write(guion)

    print("\nGUION GENERADO:\n")
    print(guion)
    print("\nGuion guardado correctamente.")

if __name__ == "__main__":
    main()
