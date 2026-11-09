import os
import re
import asyncio
from pathlib import Path

import edge_tts

from google import genai

from moviepy import (
    ImageClip,
    AudioFileClip,
    TextClip,
    CompositeVideoClip,
    concatenate_videoclips
)


# =====================================
# CONFIGURACION
# =====================================

CARPETA_ASSETS = Path("assets/gta6")

MODELO = "gemini-3.5-flash-lite"

ANCHO = 1080
ALTO = 1920

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

# Voz neuronal española
VOZ = "es-ES-AlvaroNeural"


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

    Path("guion_gta6.txt").write_text(
        texto,
        encoding="utf-8"
    )

    Path("escenas_gta6.txt").write_text(
        escenas,
        encoding="utf-8"
    )

    print("Guion generado correctamente.")

    return titulo, gancho, narracion, descripcion, hashtags


# =====================================
# GENERAR VOZ NEURONAL
# =====================================

async def generar_voz_async(texto):

    comunicacion = edge_tts.Communicate(
        text=texto,
        voice=VOZ,
        rate="+8%",
        pitch="+0Hz"
    )

    await comunicacion.save("voz.mp3")


def generar_voz(texto):

    print("Generando voz neuronal española...")

    asyncio.run(generar_voz_async(texto))

    print("Voz generada correctamente.")


# =====================================
# BUSCAR IMAGENES DE GTA VI
# =====================================

def buscar_imagenes():

    if not CARPETA_ASSETS.exists():
        raise RuntimeError(
            "No existe la carpeta assets/gta6."
        )

    extensiones = [
        "*.jpg",
        "*.jpeg",
        "*.png",
        "*.webp"
    ]

    imagenes = []

    for extension in extensiones:
        imagenes.extend(
            CARPETA_ASSETS.glob(extension)
        )

    imagenes = sorted(imagenes)

    if not imagenes:
        raise RuntimeError(
            "No hay imágenes dentro de assets/gta6. "
            "Comprueba que las has subido a GitHub."
        )

    print(f"Se han encontrado {len(imagenes)} imágenes.")

    return imagenes


# =====================================
# PREPARAR UNA IMAGEN EN FORMATO VERTICAL
# =====================================

def preparar_imagen(ruta, duracion):

    imagen = ImageClip(str(ruta)).with_duration(duracion)

    imagen = imagen.resized(height=ALTO)

    if imagen.w < ANCHO:
        imagen = imagen.resized(width=ANCHO)

    x1 = max(0, (imagen.w - ANCHO) / 2)
    y1 = max(0, (imagen.h - ALTO) / 2)

    imagen = imagen.cropped(
        x1=x1,
        y1=y1,
        x2=x1 + ANCHO,
        y2=y1 + ALTO
    )

    return imagen


# =====================================
# CREAR FONDO CON LAS IMAGENES
# =====================================

def preparar_fondo(duracion):

    imagenes = buscar_imagenes()

    tiempo_por_imagen = duracion / len(imagenes)

    clips = []

    for numero, imagen in enumerate(imagenes, start=1):

        print(
            f"Preparando imagen {numero}/{len(imagenes)}: "
            f"{imagen.name}"
        )

        clip = preparar_imagen(
            imagen,
            tiempo_por_imagen
        )

        clips.append(clip)

    fondo = concatenate_videoclips(
        clips,
        method="compose"
    )

    return fondo, clips


# =====================================
# PREPARAR SUBTITULOS
# =====================================

def dividir_subtitulos(texto):

    palabras = texto.split()
    fragmentos = []

    for i in range(0, len(palabras), 6):
        fragmentos.append(
            " ".join(palabras[i:i + 6])
        )

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

    total_caracteres = sum(
        len(x) for x in fragmentos
    )

    tiempo_actual = 0

    with open(
        "subtitulos.srt",
        "w",
        encoding="utf-8"
    ) as archivo:

        for numero, frase in enumerate(
            fragmentos,
            start=1
        ):

            tiempo_frase = (
                duracion * len(frase) / total_caracteres
            )

            inicio = tiempo_actual
            final = tiempo_actual + tiempo_frase

            archivo.write(f"{numero}\n")

            archivo.write(
                f"{tiempo_srt(inicio)} --> "
                f"{tiempo_srt(final)}\n"
            )

            archivo.write(frase + "\n\n")

            tiempo_actual = final


# =====================================
# CREAR VIDEO
# =====================================

def crear_video(titulo, gancho, narracion):

    generar_voz(narracion)

    audio = AudioFileClip("voz.mp3")
    duracion = audio.duration

    fondo, clips_imagenes = preparar_fondo(duracion)

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

    guardar_subtitulos(
        fragmentos,
        duracion
    )

    total_caracteres = sum(
        len(x) for x in fragmentos
    )

    tiempo_actual = 0

    for frase in fragmentos:

        tiempo_frase = (
            duracion * len(frase) / total_caracteres
        )

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

    # MONTAR VIDEO

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

    # CERRAR ARCHIVOS

    video_final.close()
    fondo.close()
    audio.close()

    for clip in clips_imagenes:
        clip.close()

    print("Vídeo terminado.")


# =====================================
# EJECUCION PRINCIPAL
# =====================================

def main():

    print("================================")
    print("       GTA VIRAL FACTORY")
    print("================================")

    titulo, gancho, narracion, descripcion, hashtags = generar_guion()

    crear_video(
        titulo,
        gancho,
        narracion
    )

    with open(
        "publicacion_gta6.txt",
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write("DESCRIPCION:\n")
        archivo.write(descripcion + "\n\n")

        archivo.write("HASHTAGS:\n")
        archivo.write(hashtags + "\n")

    print("================================")
    print("GTA VIRAL FACTORY COMPLETADO")
    print("================================")


if __name__ == "__main__":
    main()
