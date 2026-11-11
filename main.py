
import os
import re
import random
import asyncio
import zipfile
import urllib.request
from pathlib import Path

import yt_dlp
import edge_tts
import numpy as np

from PIL import Image, ImageDraw, ImageFont
from google import genai

from moviepy import (
    VideoFileClip,
    AudioFileClip,
    ImageClip,
    CompositeVideoClip,
    concatenate_videoclips,
)


# ==========================================================
# CONFIGURACIÓN
# ==========================================================

ANCHO = 1080
ALTO = 1920
FPS = 30

DURACION_MINIMA = 30
DURACION_MAXIMA = 40

DURACION_MINIMA_CLIP = 2.5
DURACION_MAXIMA_CLIP = 6

CARPETA_VIDEOS = Path("videos_gta6")
CARPETA_SALIDA = Path(".")

API_KEY = os.environ.get("GEMINI_API_KEY")

MODELO_GEMINI = "gemini-3.5-flash-lite"

VOZ = "es-ES-AlvaroNeural"

ROCKSTAR_ZIP = (
    "https://media-rockstargames-com.akamaized.net/"
    "VI/downloads/videos/GTAVI_Videos.zip"
)

CANAL_ROCKSTAR = (
    "https://www.youtube.com/@RockstarGames/videos"
)

FUENTE_OFICIAL = (
    "https://www.rockstargames.com/VI/media/videos"
)


# ==========================================================
# UTILIDADES
# ==========================================================

def guardar_texto(nombre, contenido):

    Path(nombre).write_text(
        contenido,
        encoding="utf-8"
    )


def limpiar_texto(texto):

    texto = re.sub(r"\s+", " ", texto)
    texto = re.sub(r"\s+([,.!?;:])", r"\1", texto)

    return texto.strip()


# ==========================================================
# GENERAR GUION CON GEMINI
# ==========================================================

def generar_guion():

    if not API_KEY:
        raise ValueError(
            "No se encuentra GEMINI_API_KEY en GitHub Secrets."
        )

    cliente = genai.Client(api_key=API_KEY)

    prompt = """
Crea un guion original para un vídeo vertical sobre GTA 6.

REQUISITOS:

- Idioma: español de España.
- Duración narrada: aproximadamente 30-40 segundos.
- Entre 75 y 95 palabras.
- Empieza con una frase gancho que despierte curiosidad.
- Narración natural, entretenida y fluida.
- Evita frases artificiales y pausas innecesarias.
- No escribas introducciones como "Hola, hoy vamos a hablar".
- No inventes personajes, misiones, mecánicas ni características.
- No presentes rumores como si fueran hechos.
- No afirmes nada que no esté confirmado oficialmente.
- Prioriza detalles interesantes relacionados con GTA 6,
  Leonida, Vice City, sus personajes o sus tráilers oficiales.
- Evita repetir temas genéricos en cada vídeo.
- No incluyas indicaciones de cámara ni instrucciones técnicas.
- Devuelve exclusivamente el texto que debe narrar la voz.
"""

    respuesta = cliente.models.generate_content(
        model=MODELO_GEMINI,
        contents=prompt
    )

    guion = limpiar_texto(respuesta.text or "")

    if len(guion.split()) < 50:
        raise ValueError(
            "Gemini ha generado un guion demasiado corto."
        )

    guardar_texto("guion_gta6.txt", guion)

    guardar_texto(
        "escenas_gta6.txt",
        "Vídeo vertical de GTA 6.\n"
        "Fondo: vídeos oficiales de Rockstar Games.\n"
        "Narración: guion_gta6.txt\n"
    )

    publicacion = (
        guion
        + "\n\n¿Ya conocías este detalle de GTA 6?\n\n"
        + "#GTA6 #GTAVI #RockstarGames #Gaming"
    )

    guardar_texto(
        "publicacion_gta6.txt",
        publicacion
    )

    print("Guion generado correctamente.")

    return guion


# ==========================================================
# DESCARGAR VÍDEOS OFICIALES DE ROCKSTAR
# ==========================================================

def descargar_zip_oficial():

    CARPETA_VIDEOS.mkdir(
        parents=True,
        exist_ok=True
    )

    archivo_zip = CARPETA_VIDEOS / "rockstar_videos.zip"

    if archivo_zip.exists():
        print("El ZIP oficial ya está descargado.")
        return

    print("Descargando vídeos oficiales de Rockstar...")

    solicitud = urllib.request.Request(
        ROCKSTAR_ZIP,
        headers={
            "User-Agent": "Mozilla/5.0"
        }
    )

    with urllib.request.urlopen(
        solicitud,
        timeout=120
    ) as respuesta:

        with open(archivo_zip, "wb") as archivo:
            archivo.write(respuesta.read())

    print("ZIP oficial descargado.")


def extraer_zip_oficial():

    archivo_zip = CARPETA_VIDEOS / "rockstar_videos.zip"

    if not archivo_zip.exists():
        return

    print("Extrayendo vídeos oficiales...")

    with zipfile.ZipFile(
        archivo_zip,
        "r"
    ) as archivo:

        archivo.extractall(CARPETA_VIDEOS)

    print("Extracción completada.")


def descargar_youtube_oficial():

    print("Buscando vídeos en el canal oficial de Rockstar...")

    opciones_busqueda = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
        "playlistend": 100,
    }

    entradas = []

    try:

        with yt_dlp.YoutubeDL(
            opciones_busqueda
        ) as ydl:

            informacion = ydl.extract_info(
                CANAL_ROCKSTAR,
                download=False
            )

            if informacion:
                entradas = informacion.get(
                    "entries",
                    []
                )

    except Exception as error:

        print(
            "No se pudo consultar YouTube:",
            error
        )

    palabras_validas = (
        "gta vi",
        "gta 6",
        "grand theft auto vi",
        "grand theft auto 6",
    )

    videos = []

    for entrada in entradas:

        if not entrada:
            continue

        titulo = (
            entrada.get("title", "")
            .lower()
        )

        if any(
            palabra in titulo
            for palabra in palabras_validas
        ):

            identificador = entrada.get("id")

            if identificador:
                videos.append(
                    identificador
                )

    if not videos:
        print(
            "YouTube no ha proporcionado vídeos nuevos. "
            "Se utilizarán los vídeos del ZIP oficial."
        )
        return

    print(
        f"Se han encontrado {len(videos)} vídeos oficiales."
    )

    opciones_descarga = {
        "format": "best[height<=1080]/best",
        "outtmpl": str(
            CARPETA_VIDEOS / "%(id)s.%(ext)s"
        ),
        "quiet": True,
        "no_warnings": True,
        "ignoreerrors": True,
        "overwrites": False,
        "noplaylist": True,
        "retries": 3,
    }

    with yt_dlp.YoutubeDL(
        opciones_descarga
    ) as ydl:

        for identificador in videos[:6]:

            url = (
                "https://www.youtube.com/watch?v="
                + identificador
            )

            try:

                print(
                    "Descargando vídeo oficial:",
                    identificador
                )

                ydl.download([url])

            except Exception as error:

                print(
                    "No se pudo descargar:",
                    error
                )


def obtener_videos():

    descargar_zip_oficial()
    extraer_zip_oficial()

    descargar_youtube_oficial()

    extensiones = (
        ".mp4",
        ".mov",
        ".webm",
        ".m4v"
    )

    archivos = []

    for archivo in CARPETA_VIDEOS.rglob("*"):

        if not archivo.is_file():
            continue

        if archivo.suffix.lower() not in extensiones:
            continue

        if archivo.name == "rockstar_videos.zip":
            continue

        archivos.append(archivo)

    archivos = list(set(archivos))

    if not archivos:

        raise RuntimeError(
            "No se han encontrado vídeos oficiales de GTA 6."
        )

    guardar_texto(
        "fuentes_gta6.txt",
        "Fuentes oficiales utilizadas:\n"
        + FUENTE_OFICIAL
        + "\n"
        + CANAL_ROCKSTAR
        + "\n\n"
        + "Solo se han utilizado materiales del canal "
        "y la página oficial de Rockstar Games.\n"
        + "La disponibilidad de estos vídeos no implica "
        "que exista permiso para reutilizarlos comercialmente. "
        "Es necesario comprobar los derechos de uso antes "
        "de publicar o monetizar el contenido.\n"
    )

    print(
        f"Vídeos disponibles para el montaje: {len(archivos)}"
    )

    return archivos


# ==========================================================
# GENERAR VOZ
# ==========================================================

async def generar_voz_async(guion):

    comunicacion = edge_tts.Communicate(
        guion,
        VOZ,
        rate="+8%"
    )

    await comunicacion.save("voz.mp3")


def generar_voz(guion):

    print("Generando narración en español...")

    asyncio.run(
        generar_voz_async(guion)
    )

    if not Path("voz.mp3").exists():
        raise RuntimeError(
            "No se ha generado el archivo de voz."
        )

    print("Voz generada correctamente.")


# ==========================================================
# PREPARAR VÍDEOS VERTICALES
# ==========================================================

def elegir_segmento(video):

    duracion = video.duration

    if duracion <= 0:
        raise ValueError(
            "El vídeo no tiene duración válida."
        )

    longitud = min(
        random.uniform(
            DURACION_MINIMA_CLIP,
            DURACION_MAXIMA_CLIP
        ),
        duracion
    )

    max_inicio = max(
        0,
        duracion - longitud
    )

    inicio = (
        random.uniform(0, max_inicio)
        if max_inicio > 0
        else 0
    )

    segmento = video.subclipped(
        inicio,
        inicio + longitud
    ).without_audio()

    # Escalar para cubrir completamente el formato vertical.
    factor = max(
        ANCHO / segmento.w,
        ALTO / segmento.h
    )

    segmento = segmento.resized(factor)

    # Recortar el centro sin dejar bandas negras.
    segmento = segmento.cropped(
        x_center=segmento.w / 2,
        y_center=segmento.h / 2,
        width=ANCHO,
        height=ALTO
    )

    return segmento


# ==========================================================
# SUBTÍTULOS
# ==========================================================

def cargar_fuente(tamano):

    posibles = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
        "/usr/share/fonts/truetype/liberation2/LiberationSans-Bold.ttf",
    ]

    for ruta in posibles:

        if Path(ruta).exists():

            return ImageFont.truetype(
                ruta,
                tamano
            )

    return ImageFont.load_default()


def dividir_lineas(texto, fuente, dibujo, ancho_maximo):

    palabras = texto.split()

    lineas = []
    actual = ""

    for palabra in palabras:

        prueba = (
            actual + " " + palabra
        ).strip()

        caja = dibujo.textbbox(
            (0, 0),
            prueba,
            font=fuente,
            stroke_width=2
        )

        ancho = caja[2] - caja[0]

        if ancho > ancho_maximo and actual:

            lineas.append(actual)
            actual = palabra

        else:
            actual = prueba

    if actual:
        lineas.append(actual)

    return lineas


def crear_imagen_texto(texto, tipo="subtitulo"):

    imagen = Image.new(
        "RGBA",
        (ANCHO, ALTO),
        (0, 0, 0, 0)
    )

    dibujo = ImageDraw.Draw(imagen)

    if tipo == "titulo":

        fuente = cargar_fuente(66)
        ancho_maximo = 900
        posicion_y = 300

    else:

        fuente = cargar_fuente(53)
        ancho_maximo = 900
        posicion_y = 1430

    lineas = dividir_lineas(
        texto,
        fuente,
        dibujo,
        ancho_maximo
    )

    alto_linea = 75
    alto_caja = len(lineas) * alto_linea + 65

    caja_superior = posicion_y
    caja_inferior = posicion_y + alto_caja

    dibujo.rounded_rectangle(
        (
            55,
            caja_superior,
            ANCHO - 55,
            caja_inferior
        ),
        radius=30,
        fill=(0, 0, 0, 190)
    )

    y = posicion_y + 25

    for linea in lineas:

        caja = dibujo.textbbox(
            (0, 0),
            linea,
            font=fuente,
            stroke_width=2
        )

        ancho_texto = caja[2] - caja[0]

        x = (ANCHO - ancho_texto) / 2

        dibujo.text(
            (x, y),
            linea,
            font=fuente,
            fill="white",
            stroke_width=2,
            stroke_fill="black"
        )

        y += alto_linea

    return np.array(imagen)


def crear_subtitulos(guion, duracion_audio):

    palabras = guion.split()

    grupos = []

    tamano_grupo = 6

    for i in range(
        0,
        len(palabras),
        tamano_grupo
    ):

        grupos.append(
            " ".join(
                palabras[
                    i:i + tamano_grupo
                ]
            )
        )

    if not grupos:
        return []

    duracion_grupo = (
        duracion_audio / len(grupos)
    )

    subtitulos = []

    for i, texto in enumerate(grupos):

        inicio = i * duracion_grupo

        imagen = crear_imagen_texto(
            texto,
            "subtitulo"
        )

        clip = (
            ImageClip(imagen)
            .with_start(inicio)
            .with_duration(duracion_grupo)
            .with_position(("center", 0))
        )

        subtitulos.append(clip)

    return subtitulos


# ==========================================================
# CREAR VÍDEO FINAL
# ==========================================================

def crear_video(guion, archivos_videos):

    print("Preparando el montaje vertical...")

    audio = AudioFileClip("voz.mp3")

    duracion_audio = audio.duration

    if duracion_audio <= 0:

        audio.close()

        raise RuntimeError(
            "La narración no tiene duración válida."
        )

    if not (
        DURACION_MINIMA <= duracion_audio <= DURACION_MAXIMA
    ):

        print(
            f"Duración de la voz: {duracion_audio:.1f} segundos."
        )

    fuentes = []
    segmentos = []
    composicion = None

    try:

        for ruta in archivos_videos:

            try:

                video = VideoFileClip(
                    str(ruta),
                    audio=False
                )

                if video.duration > 0:

                    fuentes.append(video)

            except Exception as error:

                print(
                    f"No se pudo abrir {ruta.name}: {error}"
                )

        if not fuentes:

            raise RuntimeError(
                "No se ha podido abrir ningún vídeo oficial."
            )

        # Crear suficientes fragmentos para cubrir la voz.
        duracion_total = 0

        while duracion_total < duracion_audio:

            video = random.choice(fuentes)

            segmento = elegir_segmento(video)

            restante = (
                duracion_audio - duracion_total
            )

            if segmento.duration > restante:

                segmento = segmento.subclipped(
                    0,
                    restante
                )

            segmentos.append(segmento)

            duracion_total += segmento.duration

        fondo = concatenate_videoclips(
            segmentos,
            method="compose"
        )

        fondo = fondo.subclipped(
            0,
            duracion_audio
        )

        print(
            f"Duración del fondo: {fondo.duration:.2f} segundos."
        )

        # Título inicial.
        imagen_titulo = crear_imagen_texto(
            "GTA 6: UN DETALLE QUE DEBES CONOCER",
            "titulo"
        )

        titulo = (
            ImageClip(imagen_titulo)
            .with_start(0)
            .with_duration(3.5)
            .with_position(("center", 0))
        )

        subtitulos = crear_subtitulos(
            guion,
            duracion_audio
        )

        composicion = CompositeVideoClip(
            [
                fondo,
                titulo,
                *subtitulos
            ],
            size=(ANCHO, ALTO)
        )

        composicion = (
            composicion
            .with_audio(audio)
            .with_duration(duracion_audio)
        )

        print("Renderizando vídeo final...")

        composicion.write_videofile(
            "video_gta6.mp4",
            fps=FPS,
            codec="libx264",
            audio_codec="aac",
            preset="ultrafast",
            threads=4,
            logger="bar"
        )

        print("Vídeo generado correctamente.")

    finally:

        if composicion is not None:
            composicion.close()

        for segmento in segmentos:
            try:
                segmento.close()
            except Exception:
                pass

        for video in fuentes:
            try:
                video.close()
            except Exception:
                pass

        audio.close()


# ==========================================================
# PROGRAMA PRINCIPAL
# ==========================================================

def main():

    print("======================================")
    print("       GTA VIRAL FACTORY")
    print("======================================")

    print("PASO 1: Generando guion...")

    guion = generar_guion()

    print("PASO 2: Buscando vídeos oficiales...")

    videos = obtener_videos()

    print("PASO 3: Generando voz...")

    generar_voz(guion)

    print("PASO 4: Montando vídeo vertical...")

    crear_video(
        guion,
        videos
    )

    print("PASO 5: Comprobando archivos...")

    archivos_finales = [
        "guion_gta6.txt",
        "escenas_gta6.txt",
        "fuentes_gta6.txt",
        "voz.mp3",
        "publicacion_gta6.txt",
        "video_gta6.mp4",
    ]

    for nombre in archivos_finales:

        ruta = Path(nombre)

        if not ruta.exists():
            raise RuntimeError(
                f"No se ha generado el archivo: {nombre}"
            )

        if ruta.stat().st_size == 0:
            raise RuntimeError(
                f"El archivo está vacío: {nombre}"
            )

        print(
            f"OK: {nombre} "
            f"({ruta.stat().st_size} bytes)"
        )

    print("======================================")
    print("GENERACIÓN COMPLETADA CORRECTAMENTE")
    print("======================================")


if __name__ == "__main__":
    main()
