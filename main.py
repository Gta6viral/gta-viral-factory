
import os
import time
from google import genai

def main():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Falta la clave GEMINI_API_KEY")

    print("================================")
    print("       GTA VIRAL FACTORY")
    print("================================")
    print("Conectando con Gemini...")

    client = genai.Client(api_key=api_key)

    prompt = """
    Actúa como guionista profesional de YouTube Shorts y TikTok.

    Crea un guion ORIGINAL en español de España sobre GTA 6.

    Requisitos:
    - Duración aproximada de 30 segundos.
    - Gancho potente durante los primeros 2 segundos.
    - Tres detalles interesantes de GTA 6.
    - No inventes filtraciones ni rumores.
    - Termina con una pregunta para generar comentarios.

    Devuelve:
    1. Título llamativo.
    2. Narración completa.
    3. Ideas de escenas para acompañarla.
    4. Descripción y hashtags.
    """

    response = None

    for intento in range(4):
        try:
            print(f"Intento {intento + 1} de 4...")

            response = client.models.generate_content(
                model="gemini-3.5-flash-lite",
                contents=prompt
            )

            break

        except Exception as error:
            print("Gemini no ha respondido:", error)

            if intento == 3:
                raise

            espera = 15 * (intento + 1)
            print(f"Esperando {espera} segundos...")
            time.sleep(espera)

    guion = response.text

    if not guion:
        raise RuntimeError("Gemini no ha generado ningún guion.")

    with open("guion_gta6.txt", "w", encoding="utf-8") as archivo:
        archivo.write(guion)

    print("\nGUION GENERADO CORRECTAMENTE:\n")
    print(guion)

if __name__ == "__main__":
    main()
