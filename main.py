
import os
import re
import asyncio
import random
import zipfile
import urllib.request
from pathlib import Path

import edge_tts
from google import genai
from yt_dlp import YoutubeDL

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

CARPETA_VIDEOS = Path("videos_gta6")
MODELO = "gemini-3.5-flash-lite"

ANCHO = 1080
ALTO = 1920
FPS = 30

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
VOZ = "es-ES-AlvaroNeural"

MAX_PALABRAS_SUBTITULO = 4
MAX_CARACTERES_SUBTITULO = 27

# Solo vídeos del canal oficial de Rockstar Games
CANAL_ROCKSTAR = "https://www.youtube.com/@RockstarGames/videos"

# ZIP de clips oficiales de Rockstar
ZIP_CLIPS_ROCKSTAR = (
    "https://media-rockstargames-com.akamaized.net/"
    "VI/downloads/videos/GTAVI_Videos.zip"
)

MAX_VIDEOS_YOUTUBE = 6
DURACION_MINIMA_CLIP = 2.5
DURACION_MAXIMA_CLIP = 6.0


# =====================================
# EXTRAER APARTADOS
# =====================================

def extraer_seccion(texto, nombre):
    patron = (
        rf"(?ims)^\s*{re.escape(nombre)}\s*:\s*"
        rf"(.*?)(?=^\s*[A-ZÁÉÍÓÚÑ ]{{3,}}\s*:|\Z)"
    )
    resultado = re.search(patron, texto)
    return resultado.group(1).strip() if resultado else ""


# =====================================
# GENERAR GUION
# =====================================

def generar_guion():
    api_key = os.getenv("GEMINI_API_KEY")

    if not api_key:
        raise RuntimeError(
            "Falta GEMINI_API_KEY. Comprueba los secretos de GitHub."
        )

    cliente = genai.Client(api_key=api_key)

    prompt = """
Actúa como guionista especializado en GTA 6 y vídeos cortos virales.

Crea UN tema concreto, original y visual para un Short de 30-40 segundos.
Evita datos introductorios y curiosidades genéricas.
Prioriza detalles observables en los tráilers, personajes, escenarios,
referencias y comparaciones que tengan una pista concreta.

REGLAS DE VERACIDAD:
- No inventes datos, declaraciones, funciones, fechas ni fuentes.
- No presentes teorías como hechos.
- No afirmes que una mecánica existe solo porque aparece en un tráiler.
- Si no recuerdas un detalle con seguridad, no lo uses.
- No inventes que un detalle está oculto o que nadie lo ha visto.
- El guion se verificará después con el material visual oficial.

NARRACIÓN Y VOZ:
- Español de España, natural y conversacional.
- 30-40 segundos aproximadamente.
- Escribe como una persona hablando a cámara, no como un artículo.
- Enlaza las ideas con naturalidad.
- Evita frases telegráficas, puntos suspensivos, listas y pausas dramáticas.
- No pongas una frase aislada por línea.
- Usa puntuación normal y frases de longitud variada.
- Empieza directamente con la curiosidad.
- Termina con una pregunta breve que invite a comentar.

El tema debe poder ilustrarse con vídeos oficiales de GTA 6.
No propongas escenas de GTA V ni de otros juegos.

Devuelve EXACTAMENTE:

TITULO:
GANCHO:
NARRACION:
ESCENAS:
DESCRIPCION:
HASHTAGS:
FUENTES:

En ESCENAS describe tres momentos visuales concretos que habría que localizar
en los vídeos oficiales de GTA 6. No inventes timecodes ni afirmes que una
escena aparece en un vídeo si no estás seguro.

En FUENTES indica que el guion necesita comprobación visual antes de publicar.
No inventes enlaces ni fuentes.
"""

    print("Generando guion...")

    try:
        respuesta = cliente.models.generate_content(
            model=MODELO,
            contents=prompt
        )

    except Exception as error:
        mensaje = str(error).lower()

        if (
            "429" in mensaje
            or "resource_exhausted" in mensaje
            or "quota" in mensaje
        ):
            raise RuntimeError(
                "GEMINI HA RECHAZADO LA PETICION POR CUOTA. "
                "Comprueba los límites del proyecto en Google AI Studio."
            ) from None

        raise RuntimeError(
            f"Error al conectar con Gemini: {error}"
        ) from None

    texto = respuesta.text or ""

    if not texto.strip():
        raise RuntimeError("Gemini no ha generado contenido.")

    titulo = (
        extraer_seccion(texto, "TITULO")
        or "GTA 6: EL DETALLE QUE NO VISTE"
    )

    gancho = extraer_seccion(texto, "GANCHO") or titulo
    narracion = extraer_seccion(texto, "NARRACION")
    escenas = extraer_seccion(texto, "ESCENAS")
    descripcion = extraer_seccion(texto, "DESCRIPCION")
    hashtags = extraer_seccion(texto, "HASHTAGS")

    if not narracion:
        raise RuntimeError("No se ha podido extraer la narración.")

    Path("guion_gta6.txt").write_text(
        texto,
        encoding="utf-8"
    )

    Path("escenas_gta6.txt").write_text(
        escenas,
        encoding="utf-8"
    )

    Path("fuentes_gta6.txt").write_text(
        "VERIFICACIÓN DEL CONTENIDO\n\n"
        "El guion se ha generado sin búsqueda web.\n"
        "Debe comprobarse cada afirmación contra los vídeos oficiales "
        "de GTA 6 antes de publicarlo.\n",
        encoding="utf-8"
    )

    return titulo, gancho, narracion, descripcion, hashtags


# =====================================
# DESCARGAR MATERIAL OFICIAL GTA 6
# =====================================

def es_video_gta6_oficial(entry):
    titulo = (entry.get("title") or "").lower()

    canal = (
        entry.get("channel")
        or entry.get("uploader")
        or ""
    ).strip().lower()

    canal_url = (
        entry.get("channel_url")
        or entry.get("uploader_url")
        or ""
    ).lower()

    titulo_gta6 = (
        "grand theft auto vi" in titulo
        or "grand theft auto 6" in titulo
        or "gta vi" in titulo
        or "gta 6" in titulo
    )

    canal_oficial = (
        canal == "rockstar games"
        or "@rockstargames" in canal_url
    )

    return titulo_gta6 and canal_oficial


def descargar_zip_clips():
    CARPETA_VIDEOS.mkdir(
        parents=True,
        exist_ok=True
    )

    zip_path = CARPETA_VIDEOS / "clips_oficiales_rockstar.zip"

    if not zip_path.exists() or zip_path.stat().st_size < 100_000:

        print("Descargando clips oficiales desde Rockstar...")

        request = urllib.request.Request(
            ZIP_CLIPS_ROCKSTAR,
            headers={"User-Agent": "Mozilla/5.0"}
        )

        try:
            with urllib.request.urlopen(
                request,
                timeout=90
            ) as response:
                zip_path.write_bytes(response.read())

        except Exception as error:
            print(
                f"No se pudo descargar el ZIP oficial: {error}"
            )
            return

    try:
        with zipfile.ZipFile(zip_path, "r") as archivo_zip:

            for miembro in archivo_zip.namelist():

                nombre = Path(miembro).name

                if not nombre:
                    continue

                extension = Path(nombre).suffix.lower()

                if extension not in {
                    ".mp4",
                    ".mov",
                    ".webm",
                    ".m4v"
                }:
                    continue

                destino = CARPETA_VIDEOS / nombre

                if not destino.exists():

                    with archivo_zip.open(miembro) as origen:
                        destino.write_bytes(origen.read())

        print("Clips oficiales de Rockstar revisados.")

    except Exception as error:
        print(
            f"El ZIP de clips no se pudo abrir: {error}"
        )


def descargar_videos_canal_rockstar():

    print(
        "Buscando vídeos de GTA 6 en el canal oficial de Rockstar..."
    )

    opciones = {
        "quiet": True,
        "no_warnings": True,
        "extract_flat": True,
        "skip_download": True,
        "ignoreerrors": True,
        "playlistend": 250,
    }

    try:
        with YoutubeDL(opciones) as ydl:
            info = ydl.extract_info(
                CANAL_ROCKSTAR,
                download=False
            )

    except Exception as error:
        print(
            f"No se pudo consultar el canal oficial: {error}"
        )
        return []

    entradas = info.get("entries") or []

    candidatos = [
        e for e in entradas
        if e and es_video_gta6_oficial(e)
    ]

    # Priorizar tráilers y vídeos de presentación.
    candidatos.sort(
        key=lambda e: (
            0 if any(
                p in (e.get("title") or "").lower()
                for p in (
                    "extended look",
                    "launch trailer",
                    "trailer"
                )
            ) else 1,
            -(e.get("timestamp") or 0)
        )
    )

    seleccionados = candidatos[:MAX_VIDEOS_YOUTUBE]

    if not seleccionados:
        print(
            "No se encontraron vídeos coincidentes del canal oficial."
        )
        return []

    opciones_descarga = {
        "quiet": False,
        "no_warnings": True,
        "ignoreerrors": True,
        "noplaylist": True,
        "format": (
            "bv*[ext=mp4][height<=1080]+ba[ext=m4a]"
            "/b[ext=mp4]/b"
        ),
        "merge_output_format": "mp4",
        "outtmpl": str(
            CARPETA_VIDEOS / "%(id)s.%(ext)s"
        ),
        "overwrites": False,
        "continuedl": True,
        "retries": 3,
        "fragment_retries": 3,
    }

    descargados = []

    with YoutubeDL(opciones_descarga) as ydl:

        for entrada in seleccionados:

            video_id = entrada.get("id")

            url = entrada.get("url") or (
                f"https://www.youtube.com/watch?v={video_id}"
            )

            titulo = entrada.get(
                "title",
                "Vídeo GTA 6"
            )

            print(
                f"Vídeo oficial encontrado: {titulo}"
            )

            try:
                resultado = ydl.extract_info(
                    url,
                    download=True
                )

                if resultado:

                    archivo = ydl.prepare_filename(resultado)
                    ruta = Path(archivo)

                    if ruta.suffix.lower() != ".mp4":

                        ruta_mp4 = ruta.with_suffix(".mp4")

                        if ruta_mp4.exists():
                            ruta = ruta_mp4

                    if ruta.exists() and ruta.suffix.lower() in {
                        ".mp4",
                        ".mov",
                        ".mkv",
                        ".webm"
                    }:
                        descargados.append(ruta)

            except Exception as error:
                print(
                    f"No se pudo descargar {titulo}: {error}"
                )

    return descargados


def buscar_videos():

    descargar_zip_clips()

    descargados = descargar_videos_canal_rockstar()

    extensiones = {
        ".mp4",
        ".mov",
        ".mkv",
        ".webm",
        ".m4v"
    }

    videos = sorted(
        p for p in CARPETA_VIDEOS.rglob("*")
        if p.is_file()
        and p.suffix.lower() in extensiones
        and p.stat().st_size > 500_000
    )

    # Solo se permiten vídeos oficiales de GTA 6.
    if not videos:
        raise RuntimeError(
            "No se ha encontrado ningún vídeo oficial de GTA 6. "
            "No se utilizarán imágenes ni vídeos de otros GTA."
        )

    print(
        f"Vídeos oficiales disponibles: {len(videos)}"
    )

    with open(
        "fuentes_videos_gta6.txt",
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "MATERIAL VISUAL DESCARGADO\n\n"
        )

        archivo.write(
            "Fuente oficial Rockstar Media:\n"
        )

        archivo.write(
            "https://www.rockstargames.com/VI/media/videos\n\n"
        )

        archivo.write(
            "Canal oficial de Rockstar Games:\n"
        )

        archivo.write(
            "https://www.youtube.com/@RockstarGames/videos\n\n"
        )

        archivo.write(
            "Archivos utilizados:\n"
        )

        for video in videos:
            archivo.write(
                f"- {video.name}\n"
            )

        archivo.write(
            "\nLa disponibilidad para descarga no implica por sí sola "
            "una licencia de reutilización comercial. Comprueba los "
            "derechos y condiciones antes de publicar o monetizar.\n"
        )

    return videos


# =====================================
# VOZ NATURAL Y SINCRONIZACION
# =====================================

def limpiar_narracion(texto):

    texto = texto.replace("\n", " ")
    texto = texto.replace("…", ".")
    texto = texto.replace("—", ", ")
    texto = texto.replace("–", ", ")

    texto = re.sub(
        r"\s+",
        " ",
        texto
    )

    texto = re.sub(
        r"\s+([,.!?;:])",
        r"\1",
        texto
    )

    texto = re.sub(
        r"([,.!?;:])([^\s])",
        r"\1 \2",
        texto
    )

    return texto.strip()


async def generar_voz_async(texto):

    comunicacion = edge_tts.Communicate(
        text=texto,
        voice=VOZ,
        rate="+15%",
        pitch="+0Hz"
    )

    palabras = []

    with open("voz.mp3", "wb") as audio:

        async for fragmento in comunicacion.stream():

            if fragmento["type"] == "audio":

                audio.write(
                    fragmento["data"]
                )

            elif fragmento["type"] == "WordBoundary":

                palabras.append({
                    "texto": fragmento["text"],
                    "inicio": (
                        fragmento["offset"] / 10_000_000
                    ),
                    "duracion": (
                        fragmento["duration"] / 10_000_000
                    )
                })

    return palabras


def generar_voz(texto):

    texto = limpiar_narracion(texto)

    print("Generando voz más fluida...")

    palabras = asyncio.run(
        generar_voz_async(texto)
    )

    print(
        f"Palabras sincronizadas: {len(palabras)}"
    )

    return palabras


# =====================================
# SUBTITULOS
# =====================================

def agrupar_palabras(palabras, duracion, narracion):

    grupos = []
    grupo_actual = []

    for palabra in palabras:

        texto_actual = " ".join(
            p["texto"] for p in grupo_actual
        )

        nuevo_texto = (
            texto_actual + " " + palabra["texto"]
        ).strip()

        if grupo_actual and (
            len(grupo_actual) >= MAX_PALABRAS_SUBTITULO
            or len(nuevo_texto) > MAX_CARACTERES_SUBTITULO
        ):

            grupos.append(grupo_actual)
            grupo_actual = []

        grupo_actual.append(palabra)

    if grupo_actual:
        grupos.append(grupo_actual)

    resultado = []

    for grupo in grupos:

        texto = " ".join(
            p["texto"] for p in grupo
        )

        inicio = max(
            0,
            grupo[0]["inicio"]
        )

        final = min(
            duracion,
            grupo[-1]["inicio"] + grupo[-1]["duracion"]
        )

        if final > inicio:

            resultado.append({
                "texto": texto,
                "inicio": inicio,
                "final": final
            })

    if not resultado:

        palabras_texto = narracion.split()

        bloques = [
            palabras_texto[i:i + MAX_PALABRAS_SUBTITULO]
            for i in range(
                0,
                len(palabras_texto),
                MAX_PALABRAS_SUBTITULO
            )
        ]

        total = max(
            1,
            len(palabras_texto)
        )

        tiempo = 0

        for bloque in bloques:

            siguiente = (
                tiempo + duracion * len(bloque) / total
            )

            resultado.append({
                "texto": " ".join(bloque),
                "inicio": tiempo,
                "final": siguiente
            })

            tiempo = siguiente

    return resultado


def tiempo_srt(segundos):

    horas = int(segundos // 3600)
    minutos = int((segundos % 3600) // 60)
    segundos_enteros = int(segundos % 60)
    milisegundos = int((segundos % 1) * 1000)

    return (
        f"{horas:02}:{minutos:02}:{segundos_enteros:02},"
        f"{milisegundos:03}"
    )


def guardar_subtitulos(grupos):

    with open(
        "subtitulos.srt",
        "w",
        encoding="utf-8"
    ) as archivo:

        for numero, grupo in enumerate(
            grupos,
            start=1
        ):

            archivo.write(
                f"{numero}\n"
            )

            archivo.write(
                f"{tiempo_srt(grupo['inicio'])} --> "
                f"{tiempo_srt(grupo['final'])}\n"
            )

            archivo.write(
                grupo["texto"] + "\n\n"
            )


# =====================================
# MONTAR FONDO CON VIDEO REAL
# =====================================

def elegir_segmento(video):

    duracion = video.duration

    if duracion <= DURACION_MINIMA_CLIP:
        return video.without_audio()

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
    )

    segmento = segmento.without_audio()

    # Adaptar el vídeo a formato vertical.
    segmento = segmento.resized(
        height=ALTO
    )

    ancho_actual = segmento.w

    if ancho_actual < ANCHO:

        segmento = segmento.resized(
            width=ANCHO
        )

        ancho_actual = segmento.w

    segmento = segmento.cropped(
        x_center=ancho_actual / 2,
        y_center=ALTO / 2,
        width=ANCHO,
        height=ALTO
    )

    return segmento


def preparar_fondo_video(duracion_audio):

    rutas = buscar_videos()

    random.shuffle(rutas)

    clips = []
    fuentes_abiertas = []

    duracion_acumulada = 0
    indice = 0

    while duracion_acumulada < duracion_audio:

        ruta = rutas[indice % len(rutas)]

        indice += 1
        fuente = None

        try:

            fuente = VideoFileClip(
                str(ruta),
                audio=False
            )

            if fuente.duration < 1:

                fuente.close()
                continue

            segmento = elegir_segmento(fuente)

            clips.append(segmento)
            fuentes_abiertas.append(fuente)

            duracion_acumulada += segmento.duration

        except Exception as error:

            print(
                f"No se pudo utilizar {ruta.name}: {error}"
            )

            if fuente:

                try:
                    fuente.close()
                except Exception:
                    pass

            if indice >= len(rutas) * 2 and not clips:

                raise RuntimeError(
                    "No se ha podido abrir ningún vídeo oficial de GTA 6."
                )

        if indice > len(rutas) * 10:

            raise RuntimeError(
                "No se ha podido completar el fondo con vídeos oficiales."
            )

    fondo = concatenate_videoclips(
        clips,
        method="compose"
    )

    fondo = fondo.subclipped(
        0,
        duracion_audio
    )

    return fondo, clips, fuentes_abiertas


# =====================================
# TEXTO EN PANTALLA
# =====================================

def crear_texto(texto, tamano, color, ancho, alto):

    return TextClip(
        font=FUENTE,
        text=texto,
        font_size=tamano,
        color=color,
        stroke_color="black",
        stroke_width=4,
        method="caption",
        size=(ancho, alto),
        text_align="center"
    )


# =====================================
# CREAR VIDEO FINAL
# =====================================

def crear_video(titulo, gancho, narracion):

    narracion_limpia = limpiar_narracion(
        narracion
    )

    palabras = generar_voz(
        narracion_limpia
    )

    audio = AudioFileClip(
        "voz.mp3"
    )

    duracion = audio.duration

    fondo, clips_video, fuentes_video = preparar_fondo_video(
        duracion
    )

    capas = [fondo]

    texto_titulo = crear_texto(
        titulo[:100],
        58,
        "yellow",
        960,
        250
    ).with_duration(
        min(2.8, duracion)
    ).with_position(
        ("center", 150)
    )

    capas.append(texto_titulo)

    if gancho:

        texto_gancho = crear_texto(
            gancho[:120],
            43,
            "white",
            940,
            210
        ).with_duration(
            min(2.3, duracion)
        ).with_position(
            ("center", 470)
        )

        capas.append(texto_gancho)

    grupos = agrupar_palabras(
        palabras,
        duracion,
        narracion_limpia
    )

    guardar_subtitulos(grupos)

    for grupo in grupos:

        subtitulo = crear_texto(
            grupo["texto"],
            54,
            "white",
            960,
            180
        )

        inicio = max(
            0,
            grupo["inicio"] - 0.02
        )

        final = min(
            duracion,
            grupo["final"] + 0.10
        )

        subtitulo = (
            subtitulo
            .with_start(inicio)
            .with_duration(
                max(0.1, final - inicio)
            )
            .with_position(
                ("center", 1430)
            )
        )

        capas.append(subtitulo)

    marca = TextClip(
        font=FUENTE,
        text="GTA VIRAL FACTORY",
        font_size=27,
        color="white",
        stroke_color="black",
        stroke_width=2
    ).with_duration(
        duracion
    ).with_position(
        ("center", 1820)
    )

    capas.append(marca)

    print(
        "Montando Short vertical con gameplay/tráilers de GTA 6..."
    )

    video_final = (
        CompositeVideoClip(
            capas,
            size=(ANCHO, ALTO)
        )
        .with_duration(duracion)
        .with_audio(audio)
    )

    video_final.write_videofile(
        "video_gta6.mp4",
        fps=FPS,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2
    )

    video_final.close()
    fondo.close()
    audio.close()

    for clip in clips_video:

        try:
            clip.close()
        except Exception:
            pass

    for fuente in fuentes_video:

        try:
            fuente.close()
        except Exception:
            pass

    print(
        "Vídeo terminado correctamente."
    )


# =====================================
# PUBLICACION
# =====================================

def guardar_publicacion(descripcion, hashtags):

    with open(
        "publicacion_gta6.txt",
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "DESCRIPCION:\n"
        )

        archivo.write(
            descripcion + "\n\n"
        )

        archivo.write(
            "HASHTAGS:\n"
        )

        archivo.write(
            hashtags + "\n"
        )


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

    guardar_publicacion(
        descripcion,
        hashtags
    )

    print("================================")
    print("GTA VIRAL FACTORY COMPLETADO")
    print("================================")


if __name__ == "__main__":

    try:
        main()

    except Exception as error:

        print("\n")
        print("================================")
        print("       ERROR EN GTA VIRAL FACTORY")
        print("================================")

        print(str(error))

        raise
