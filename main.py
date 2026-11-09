
import os
import re
import requests
from pathlib import Path
from datetime import datetime

from google import genai
from gtts import gTTS

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips
)


# =====================================
# CONFIGURACION
# =====================================

CARPETA = Path(".")
CARPETA_ASSETS = Path("assets/gta6")

MODELO = "gemini-3.5-flash-lite"

ANCHO = 1080
ALTO = 1920

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"


# =====================================
# GENERAR GUION
# =====================================

def extraer_seccion(texto, nombre):

    patron = (
        rf"(?ims)^\s*{re.escape(nombre)}\s*:\s*"
        rf"(.*?)(?=^\s*[A-ZÁÉÍÓÚÑ ]{{3,}}\s*:|\Z)"
    )

    resultado = re.search(patron, texto)

    if resultado:
        return resultado.group(1).strip()

    return ""


def generar_guion():

    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError("Falta GEMINI_API_KEY")

    cliente = genai.Client(api_key=api_key)

    prompt = """
Actúa como un guionista profesional especializado en
YouTube Shorts, TikTok y GTA 6.

Crea un vídeo ORIGINAL en español de España.

ESTILO:
- Mezcla de noticias, curiosidades y contenido cinematográfico.
- Narración muy enérgica y natural.
- Ritmo rápido.
- Frases cortas y fáciles de entender.
- Nada de introducciones aburridas.

ESTRUCTURA:
- Gancho muy potente en los primeros 2 segundos.
- Explicación interesante.
- Tres detalles o ideas relevantes.
- Cierre con una pregunta para conseguir comentarios.

DURACIÓN:
Entre 30 y 40 segundos de narración.

REGLAS IMPORTANTES:
- No inventes filtraciones.
- No inventes anuncios de Rockstar.
- No presentes rumores como hechos.
- No inventes fechas ni características del juego.
- Distingue claramente información confirmada de especulación.
- Si no puedes confirmar una noticia reciente, utiliza una curiosidad
  o un tema general en lugar de inventar una noticia.

Devuelve EXACTAMENTE estos apartados:

TITULO:
Un título llamativo.

GANCHO:
La primera frase que captará la atención.

NARRACION:
El texto completo que se escuchará en el vídeo.
Debe sonar natural y enérgico.

ESCENAS:
Tres ideas visuales relacionadas con GTA 6.
Una por línea.

DESCRIPCION:
Descripción para YouTube y TikTok.

HASHTAGS:
Entre cinco y ocho hashtags.

No añadas explicaciones fuera de estos apartados.
"""

    print("Conectando con Gemini...")

    respuesta = cliente.models.generate_content(
        model=MODELO,
        contents=prompt
    )

    texto = respuesta.text

    if not texto:
        raise RuntimeError("Gemini no ha generado contenido.")

    titulo = extraer_seccion(texto, "TITULO")
    gancho = extraer_seccion(texto, "GANCHO")
    narracion = extraer_seccion(texto, "NARRACION")
    escenas = extraer_seccion(texto, "ESCENAS")
    descripcion = extraer_seccion(texto, "DESCRIPCION")
    hashtags = extraer_seccion(texto, "HASHTAGS")

    if not narracion:
        raise RuntimeError("No se ha podido extraer la narración.")

    if not titulo:
        titulo = "GTA 6: DETALLES QUE DEBES CONOCER"

    with open("guion_gta6.txt", "w", encoding="utf-8") as archivo:
        archivo.write(texto)

    with open("escenas_gta6.txt", "w", encoding="utf-8") as archivo:
        archivo.write(escenas)

    print("Guion generado correctamente.")

    return titulo, gancho, narracion, descripcion, hashtags


# =====================================
# DESCARGAR FONDO PROVISIONAL
# =====================================

def descargar_video():

    api_key = os.getenv("PIXABAY_API_KEY")

    if not api_key:
        raise RuntimeError("Falta PIXABAY_API_KEY")

    print("Buscando fondo de vídeo...")

    url = "https://pixabay.com/api/videos/"

    parametros = {
        "key": api_key,
        "q": "miami neon night cars",
        "per_page": 3,
        "safesearch": "true",
        "video_type": "film"
    }

    respuesta = requests.get(
        url,
        params=parametros,
        timeout=30
    )

    respuesta.raise_for_status()

    resultados = respuesta.json().get("hits", [])

    if not resultados:
        raise RuntimeError("Pixabay no ha encontrado vídeos.")

    video = resultados[0]

    video_url = video["videos"]["medium"]["url"]

    descarga = requests.get(video_url, timeout=90)
    descarga.raise_for_status()

    with open("fondo.mp4", "wb") as archivo:
        archivo.write(descarga.content)

    with open("credito_pixabay.txt", "w", encoding="utf-8") as archivo:
        archivo.write(
            "Vídeo de Pixabay\n"
            + video["pageURL"]
            + "\nAutor: "
            + video["user"]
        )

    print("Fondo descargado.")


# =====================================
# PREPARAR SUBTITULOS
# =====================================

def dividir_subtitulos(texto):

    palabras = texto.split()
    fragmentos = []

    for i in range(0, len(palabras), 6):
        fragmentos.append(" ".join(palabras[i:i + 6]))

    return fragmentos


def tiempo_srt(segundos):

    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos_enteros = int(segundos % 60)
    milisegundos = int((segundos % 1) * 1000)

    return (
        f"{horas:02}:{minutos:02}:{segundos_enteros:02},"
        f"{milisegundos:03}"
    )


def guardar_subtitulos(fragmentos, duracion):

    total_caracteres = sum(len(x) for x in fragmentos)

    tiempo_actual = 0

    with open("subtitulos.srt", "w", encoding="utf-8") as archivo:

        for numero, frase in enumerate(fragmentos, start=1):

            tiempo_frase = (
                duracion * len(frase) / total_caracteres
            )

            inicio = tiempo_actual
            final = tiempo_actual + tiempo_frase

            archivo.write(f"{numero}\n")
            archivo.write(
                f"{tiempo_srt(inicio)} --> {tiempo_srt(final)}\n"
            )
            archivo.write(frase + "\n\n")

            tiempo_actual = final


# =====================================
# PREPARAR FONDO VERTICAL
# =====================================

def preparar_fondo(duracion):

    original = VideoFileClip("fondo.mp4")

    if original.duration < duracion:

        repeticiones = int(duracion / original.duration) + 1

        fondo = concatenate_videoclips(
            [original] * repeticiones
        )

    else:

        fondo = original

    fondo = fondo.subclipped(0, duracion)
    fondo = fondo.without_audio()

    fondo = fondo.resized(height=ALTO)

    if fondo.w > ANCHO:

        fondo = fondo.cropped(
            x1=(fondo.w - ANCHO) / 2,
            x2=(fondo.w + ANCHO) / 2,
            y1=0,
            y2=ALTO
        )

    else:

        fondo = fondo.resized(width=ANCHO)

        fondo = fondo.cropped(
            x1=0,
            x2=ANCHO,
            y1=(fondo.h - ALTO) / 2,
            y2=(fondo.h + ALTO) / 2
        )

    return original, fondo


# =====================================
# CREAR VIDEO
# =====================================

def crear_video(titulo, gancho, narracion):

    print("Generando voz española...")

    voz = gTTS(
        text=narracion,
        lang="es",
        slow=False
    )

    voz.save("voz.mp3")

    audio = AudioFileClip("voz.mp3")
    duracion = audio.duration

    original, fondo = preparar_fondo(duracion)

    capas = [fondo]

    # TITULO INICIAL

    texto_titulo = TextClip(
        font=FUENTE,
        text=titulo[:100],
        font_size=68,
        color="yellow",
        stroke_color="black",
        stroke_width=4,
        method="caption",
        size=(980, 350),
        text_align="center"
    )

    texto_titulo = (
        texto_titulo
        .with_duration(min(4, duracion))
        .with_position(("center", 180))
    )

    capas.append(texto_titulo)

    # GANCHO

    if gancho:

        texto_gancho = TextClip(
            font=FUENTE,
            text=gancho[:120],
            font_size=48,
            color="white",
            stroke_color="black",
            stroke_width=3,
            method="caption",
            size=(940, 250),
            text_align="center"
        )

        texto_gancho = (
            texto_gancho
            .with_duration(min(4, duracion))
            .with_position(("center", 650))
        )

        capas.append(texto_gancho)

    # SUBTITULOS

    fragmentos = dividir_subtitulos(narracion)

    guardar_subtitulos(fragmentos, duracion)

    total_caracteres = sum(len(x) for x in fragmentos)

    tiempo_actual = 0

    for frase in fragmentos:

        tiempo_frase = duracion * len(frase) / total_caracteres

        subtitulo = TextClip(
            font=FUENTE,
            text=frase,
            font_size=48,
            color="white",
            stroke_color="black",
            stroke_width=4,
            method="caption",
            size=(960, 230),
            text_align="center"
        )

        subtitulo = (
            subtitulo
            .with_start(tiempo_actual)
            .with_duration(tiempo_frase)
            .with_position(("center", 1450))
        )

        capas.append(subtitulo)

        tiempo_actual += tiempo_frase

    # MARCA DEL CANAL

    marca = TextClip(
        font=FUENTE,
        text="GTA VIRAL FACTORY",
        font_size=27,
        color="white",
        stroke_color="black",
        stroke_width=2
    )

    marca = (
        marca
        .with_duration(duracion)
        .with_position(("center", 1840))
    )

    capas.append(marca)

    print("Montando vídeo vertical...")

    video_final = CompositeVideoClip(
        capas,
        size=(ANCHO, ALTO)
    ).with_duration(duracion).with_audio(audio)

    video_final.write_videofile(
        "video_gta6.mp4",
        fps=24,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2
    )

    video_final.close()
    original.close()
    audio.close()

    print("Vídeo terminado.")


# =====================================
# EJECUCION PRINCIPAL
# =====================================

def main():

    print("================================")
    print("       GTA VIRAL FACTORY")
    print("================================")

    titulo, gancho, narracion, descripcion, hashtags = generar_guion()

    descargar_video()

    crear_video(titulo, gancho, narracion)

    with open("publicacion_gta6.txt", "w", encoding="utf-8") as archivo:

        archivo.write("DESCRIPCION:\n")
        archivo.write(descripcion + "\n\n")

        archivo.write("HASHTAGS:\n")
        archivo.write(hashtags + "\n")

    print("================================")
    print("GTA VIRAL FACTORY COMPLETADO")
    print("================================")


if __name__ == "__main__":
    main()
