
import os
import re
import requests
from gtts import gTTS
from google import genai
from moviepy import (
    VideoFileClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips
)

def generar_guion():
    api_key = os.getenv("GEMINI_API_KEY")
    client = genai.Client(api_key=api_key)

    prompt = """
    Escribe un guion ORIGINAL para un YouTube Short sobre GTA 6.
    Español de España. Unos 30 segundos.
    No inventes rumores ni filtraciones.

    Devuelve exactamente estos apartados:

    TÍTULO:
    Un título llamativo.

    NARRACIÓN:
    El texto completo que debe decir la voz.

    ESCENAS:
    Tres ideas visuales.

    DESCRIPCIÓN:
    Una descripción y hashtags.
    """

    response = client.models.generate_content(
        model="gemini-3.5-flash-lite",
        contents=prompt
    )

    texto = response.text

    coincidencia = re.search(
        r"NARRACIÓN\s*:\s*(.*?)(?=\n\s*ESCENAS\s*:|\n\s*DESCRIPCIÓN\s*:|$)",
        texto,
        re.IGNORECASE | re.DOTALL
    )

    if not coincidencia:
        raise RuntimeError("No se ha podido extraer la narración.")

    narracion = coincidencia.group(1).strip()

    titulo_match = re.search(
        r"TÍTULO\s*:\s*(.*?)(?=\n\s*NARRACIÓN\s*:|$)",
        texto,
        re.IGNORECASE | re.DOTALL
    )

    titulo = titulo_match.group(1).strip() if titulo_match else "GTA 6"

    with open("guion_gta6.txt", "w", encoding="utf-8") as f:
        f.write(texto)

    return titulo, narracion


def descargar_video():
    api_key = os.getenv("PIXABAY_API_KEY")

    if not api_key:
        raise RuntimeError("Falta PIXABAY_API_KEY")

    url = "https://pixabay.com/api/videos/"

    parametros = {
        "key": api_key,
        "q": "night city cars",
        "per_page": 3,
        "safesearch": "true",
        "video_type": "film"
    }

    respuesta = requests.get(url, params=parametros, timeout=30)
    respuesta.raise_for_status()

    resultados = respuesta.json().get("hits", [])

    if not resultados:
        raise RuntimeError("Pixabay no ha encontrado vídeos.")

    video = resultados[0]
    video_url = video["videos"]["medium"]["url"]

    descarga = requests.get(video_url, timeout=60)
    descarga.raise_for_status()

    with open("fondo.mp4", "wb") as f:
        f.write(descarga.content)

    with open("credito_pixabay.txt", "w", encoding="utf-8") as f:
        f.write(
            "Vídeo de Pixabay\n"
            + video["pageURL"]
            + "\nAutor: "
            + video["user"]
        )


def crear_video(titulo, narracion):
    voz = gTTS(text=narracion, lang="es")
    voz.save("voz.mp3")

    audio = AudioFileClip("voz.mp3")
    duracion = audio.duration

    fondo_original = VideoFileClip("fondo.mp4")

    if fondo_original.duration < duracion:
        repeticiones = int(duracion / fondo_original.duration) + 1
        fondo = concatenate_videoclips(
            [fondo_original] * repeticiones
        )
    else:
        fondo = fondo_original

    fondo = fondo.subclipped(0, duracion)
    fondo = fondo.without_audio()
    fondo = fondo.resized(height=1920)

    if fondo.w >= 1080:
        fondo = fondo.cropped(
            x1=(fondo.w - 1080) / 2,
            x2=(fondo.w + 1080) / 2,
            y1=0,
            y2=1920
        )
    else:
        fondo = fondo.resized(width=1080)
        fondo = fondo.cropped(
            x1=0,
            x2=1080,
            y1=(fondo.h - 1920) / 2,
            y2=(fondo.h + 1920) / 2
        )

    fuente = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

    texto_titulo = TextClip(
        font=fuente,
        text=titulo[:90],
        font_size=65,
        color="yellow",
        stroke_color="black",
        stroke_width=3,
        method="caption",
        size=(980, 300),
        text_align="center"
    ).with_duration(min(6, duracion)).with_position(("center", 150))

    texto_narracion = TextClip(
        font=fuente,
        text=narracion,
        font_size=38,
        color="white",
        stroke_color="black",
        stroke_width=2,
        method="caption",
        size=(940, 650),
        text_align="center"
    ).with_duration(duracion).with_position(("center", "bottom"))

    video_final = CompositeVideoClip(
        [fondo, texto_titulo, texto_narracion],
        size=(1080, 1920)
    ).with_duration(duracion).with_audio(audio)

    video_final.write_videofile(
        "video_gta6.mp4",
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast"
    )

    video_final.close()
    fondo_original.close()
    audio.close()


def main():
    print("GTA VIRAL FACTORY")
    print("Generando guion...")

    titulo, narracion = generar_guion()

    print("Buscando vídeo de fondo...")
    descargar_video()

    print("Creando vídeo vertical...")
    crear_video(titulo, narracion)

    print("VÍDEO CREADO CORRECTAMENTE")


if __name__ == "__main__":
    main()
