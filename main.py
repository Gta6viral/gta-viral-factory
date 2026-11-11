import os
import re
import asyncio
import shutil
from pathlib import Path

import edge_tts
from google import genai

from PIL import (
    Image,
    ImageOps,
    ImageFilter,
    ImageEnhance
)

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
CARPETA_PROCESADAS = Path("frames_gta6")

MODELO = "gemini-3.5-flash-lite"

ANCHO = 1080
ALTO = 1920

FUENTE = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"

VOZ = "es-ES-AlvaroNeural"

MAX_PALABRAS_SUBTITULO = 4
MAX_CARACTERES_SUBTITULO = 27


# =====================================
# EXTRAER APARTADOS
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
Actúa como un investigador y guionista especializado en
GTA 6 y en contenido corto viral de videojuegos.

Tu trabajo NO es explicar GTA 6 de forma básica.

Tu trabajo es encontrar un detalle, conexión, comparación,
pista o curiosidad que haga que una persona que ya conoce GTA
quiera seguir viendo el vídeo.

IMPORTANTE:

No tienes que utilizar herramientas de búsqueda externas.
Trabaja únicamente con información que conozcas con suficiente seguridad.

========================================
OBJETIVO PRINCIPAL
========================================

Crea UN SOLO TEMA FUERTE para un vídeo de 30-40 segundos.

El tema debe responder a una pregunta como:

"¿Cómo es posible que casi nadie se haya fijado en esto?"

"¿Qué detalle del tráiler tiene más importancia de la que parece?"

"¿Qué conexión con otro GTA se puede pasar por alto?"

"¿Qué pequeño detalle cambia la forma de interpretar esta escena?"

"¿Qué pista aparece en GTA 6 que puede tener una explicación?"

NO hagas una lista de datos básicos.

El vídeo debe girar alrededor de UNA curiosidad principal.

========================================
TEMAS QUE DEBES EVITAR
========================================

NO elijas como tema principal:

- Que GTA 6 está ambientado en Vice City.
- Que Lucia es protagonista.
- Que Jason es protagonista.
- Que GTA 6 es la nueva entrega.
- Que el mapa será grande.
- Que habrá vehículos.
- Que habrá policía.
- Que habrá animales.
- Que Rockstar desarrolla el juego.
- Que el juego está ambientado en Florida/Leonida.
- Información general que cualquier persona que haya visto
  un tráiler conoce.
- Rankings genéricos.
- "5 cosas que sabemos de GTA 6".
- Noticias inventadas.
- Rumores presentados como hechos.
- Especulaciones sin ninguna pista que las apoye.

Si el tema podría aparecer en un artículo introductorio
sobre GTA 6, probablemente es demasiado básico.

========================================
TIPOS DE CONTENIDO PRIORITARIOS
========================================

Prioriza, en este orden:

1. DETALLES OCULTOS
Pequeños elementos visuales, escenas, objetos, comportamientos
o situaciones que puedan pasar desapercibidos.

2. REFERENCIAS
Conexiones con GTA Vice City, GTA V, GTA IV, Red Dead Redemption
u otros elementos conocidos de Rockstar cuando la conexión sea
realmente razonable.

3. COMPARACIONES
Cambios o diferencias interesantes entre imágenes, escenas,
tráilers o conceptos conocidos.

4. DETALLES DEL MUNDO
Elementos que revelen cómo podría funcionar el mundo del juego,
siempre diferenciando claramente hechos de interpretación.

5. PERSONAJES
Detalles de personalidad, relaciones, comportamiento o escenas
que permitan una interpretación interesante.

6. ROCKSTAR
Detalles documentados sobre decisiones, desarrollo o antecedentes
de Rockstar relacionados con GTA 6.

7. MISTERIOS Y TEORÍAS
Solo si existe una pista concreta que permita plantearlas.
Debes decir claramente que se trata de una teoría.

========================================
REGLAS DE VERACIDAD
========================================

Estas reglas son obligatorias:

- No inventes información.
- No inventes cifras.
- No inventes fechas.
- No inventes declaraciones de Rockstar.
- No inventes nombres.
- No inventes características del juego.
- No presentes rumores como hechos.
- No presentes teorías como hechos.
- No confundas GTA 5 con GTA 6.
- No atribuyas a Rockstar algo que no haya confirmado.
- No digas "Rockstar confirmó" si no tienes seguridad.
- No inventes fuentes.
- No inventes enlaces.
- No afirmes que algo es una noticia reciente.
- Si un dato no es suficientemente seguro, elimínalo.

IMPORTANTE:

Una teoría puede aparecer, pero debe utilizar expresiones como:

"Una teoría plantea que..."

"Esto podría significar..."

"Algunos fans creen que..."

"Una posible explicación sería..."

Nunca:

"Esto demuestra que..."

si realmente no está confirmado.

========================================
VALOR PARA EL ESPECTADOR
========================================

Antes de escribir el guion, piensa:

¿Por qué alguien debería saber esto?

Si la respuesta es simplemente:

"porque es información sobre GTA 6",

el tema es demasiado básico.

El espectador debe terminar pensando:

"Eso no lo había visto."

o:

"Ahora quiero volver a mirar el tráiler."

o:

"¿Y si realmente significa eso?"

========================================
ESTRUCTURA
========================================

GANCHO:

Empieza directamente con el detalle.

Ejemplos de estructura:

"Hay un detalle en el tráiler de GTA 6 que probablemente
te pasó completamente desapercibido."

"Este personaje hace algo durante unos segundos y puede
tener más importancia de la que parece."

"Rockstar escondió una referencia en esta escena de GTA 6
y es muy fácil pasarla por alto."

No copies literalmente estos ejemplos.

NARRACIÓN:

- 30-40 segundos.
- Ritmo rápido.
- Frases cortas.
- Explicación clara.
- Una curiosidad principal.
- Añade contexto suficiente para entenderla.
- Termina con una pregunta que invite a comentar.

No llenes el vídeo con tres curiosidades independientes.

========================================
CALIDAD DEL TEMA
========================================

Antes de devolver el resultado, haz internamente este filtro:

PUNTUACIÓN DEL TEMA:

Originalidad: 0-10
Interés: 0-10
Nivel de conocimiento requerido: 0-10
Potencial para generar comentarios: 0-10

Si el tema obtiene menos de 7 en originalidad,
descártalo y busca otro.

Si el tema es demasiado conocido,
descártalo.

Si el tema depende de un dato que no puedes verificar con seguridad,
descártalo.

========================================
NO REPETIR
========================================

Evita producir constantemente el mismo tipo de vídeo.

Alterna entre:

- detalle visual
- referencia
- comparación
- personaje
- mundo
- desarrollo
- misterio
- teoría

No uses siempre "el tráiler esconde..." como estructura.

========================================
ESTILO
========================================

Español de España.

Energético.

Natural.

Moderno.

Como un creador especializado en GTA.

Nada de lenguaje académico.

Nada de frases artificiales.

Nada de introducciones largas.

Nada de:

"Hola chicos, bienvenidos..."

Empieza directamente con la curiosidad.

========================================
TÍTULO
========================================

El título debe crear curiosidad sin mentir.

Ejemplos de estilo:

"El detalle de GTA 6 que casi nadie vio"

"Rockstar escondió esto en GTA 6"

"Esta escena de GTA 6 tiene un detalle MUY raro"

"¿Te fijaste en esto durante el tráiler?"

No copies estos títulos literalmente.

========================================
ESCENAS
========================================

Propón tres escenas visuales.

Deben estar relacionadas directamente con la narración.

No pongas simplemente:

"Imagen de GTA 6"

Describe qué debería aparecer.

Ejemplo:

"Plano cercano del personaje mientras ocurre el detalle mencionado."

"Imagen del tráiler mostrando el elemento concreto."

"Comparación visual con una escena relacionada de GTA anterior."

========================================
FUENTES
========================================

No inventes fuentes.

Como no se utiliza búsqueda web en esta generación,
indica claramente que el contenido debe verificarse antes
de publicarse.

========================================
FORMATO OBLIGATORIO
========================================

Devuelve EXACTAMENTE estos apartados:

TITULO:
Título llamativo y curioso.

GANCHO:
Primera frase del vídeo.

NARRACION:
Texto completo de 30-40 segundos.

ESCENAS:
Tres escenas visuales.
Una por línea.

DESCRIPCION:
Descripción breve para YouTube Shorts y TikTok.

HASHTAGS:
Entre cinco y ocho hashtags relevantes.

FUENTES:
Explicación breve indicando que no se ha utilizado búsqueda web
en esta generación y que los datos deben verificarse antes
de publicar.

No añadas explicaciones fuera de estos apartados.
"""

    print("Generando guion especializado...")
    print("Modo gratuito: búsqueda web desactivada.")

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
                "Comprueba los límites del proyecto en Google AI Studio. "
                "Quitar Google Search no elimina los límites de uso "
                "del propio modelo."
            ) from None

        raise RuntimeError(
            f"Error al conectar con Gemini: {error}"
        ) from None

    texto = respuesta.text

    if not texto:
        raise RuntimeError(
            "Gemini no ha generado contenido."
        )

    titulo = extraer_seccion(texto, "TITULO")
    gancho = extraer_seccion(texto, "GANCHO")
    narracion = extraer_seccion(texto, "NARRACION")
    escenas = extraer_seccion(texto, "ESCENAS")
    descripcion = extraer_seccion(texto, "DESCRIPCION")
    hashtags = extraer_seccion(texto, "HASHTAGS")

    if not narracion:
        raise RuntimeError(
            "No se ha podido extraer la narración del guion."
        )

    if not titulo:
        titulo = "GTA 6: EL DETALLE QUE CASI NADIE VIO"

    if not gancho:
        gancho = titulo

    Path("guion_gta6.txt").write_text(
        texto,
        encoding="utf-8"
    )

    Path("escenas_gta6.txt").write_text(
        escenas,
        encoding="utf-8"
    )

    with open(
        "fuentes_gta6.txt",
        "w",
        encoding="utf-8"
    ) as archivo:

        archivo.write(
            "FUENTES Y VERIFICACION\n\n"
            "Esta generación no ha utilizado Google Search.\n"
            "El guion se ha creado con el conocimiento del modelo.\n"
            "El sistema prioriza curiosidades y detalles poco conocidos,\n"
            "pero los datos deben comprobarse antes de publicar.\n"
        )

    print("Guion especializado generado correctamente.")

    return (
        titulo,
        gancho,
        narracion,
        descripcion,
        hashtags
    )


# =====================================
# GENERAR VOZ Y CAPTURAR PALABRAS
# =====================================

async def generar_voz_async(texto):

    comunicacion = edge_tts.Communicate(
        text=texto,
        voice=VOZ,
        rate="+8%",
        pitch="+0Hz"
    )

    palabras = []

    with open("voz.mp3", "wb") as audio:

        async for fragmento in comunicacion.stream():

            if fragmento["type"] == "audio":

                audio.write(fragmento["data"])

            elif fragmento["type"] == "WordBoundary":

                palabras.append({
                    "texto": fragmento["text"],
                    "inicio": fragmento["offset"] / 10_000_000,
                    "duracion": fragmento["duration"] / 10_000_000
                })

    return palabras


def generar_voz(texto):

    print("Generando voz y sincronizando palabras...")

    palabras = asyncio.run(
        generar_voz_async(texto)
    )

    print(
        f"Palabras sincronizadas: {len(palabras)}"
    )

    return palabras


# =====================================
# AGRUPAR PALABRAS PARA SUBTITULOS
# =====================================

def agrupar_palabras(palabras, duracion):

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

        inicio = grupo[0]["inicio"]

        final = (
            grupo[-1]["inicio"] +
            grupo[-1]["duracion"]
        )

        inicio = max(0, inicio)
        final = min(duracion, final)

        if final <= inicio:
            continue

        resultado.append({
            "texto": texto,
            "inicio": inicio,
            "final": final
        })

    if not resultado:

        print(
            "Usando sincronización alternativa de subtítulos."
        )

        texto_completo = Path(
            "guion_gta6.txt"
        ).read_text(encoding="utf-8")

        narracion = extraer_seccion(
            texto_completo,
            "NARRACION"
        )

        palabras_texto = narracion.split()

        bloques = [
            palabras_texto[i:i + MAX_PALABRAS_SUBTITULO]
            for i in range(
                0,
                len(palabras_texto),
                MAX_PALABRAS_SUBTITULO
            )
        ]

        total = max(1, len(palabras_texto))
        tiempo = 0

        for bloque in bloques:

            peso = len(bloque) / total
            siguiente = tiempo + duracion * peso

            resultado.append({
                "texto": " ".join(bloque),
                "inicio": tiempo,
                "final": siguiente
            })

            tiempo = siguiente

    return resultado


# =====================================
# FORMATO SRT
# =====================================

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

            archivo.write(f"{numero}\n")

            archivo.write(
                f"{tiempo_srt(grupo['inicio'])} --> "
                f"{tiempo_srt(grupo['final'])}\n"
            )

            archivo.write(
                grupo["texto"] + "\n\n"
            )


# =====================================
# ENCONTRAR IMAGENES
# =====================================

def buscar_imagenes():

    if not CARPETA_ASSETS.exists():

        raise RuntimeError(
            "No existe la carpeta assets/gta6."
        )

    extensiones = {
        ".jpg",
        ".jpeg",
        ".png",
        ".webp"
    }

    imagenes = [
        ruta
        for ruta in CARPETA_ASSETS.rglob("*")
        if ruta.is_file()
        and ruta.suffix.lower() in extensiones
    ]

    imagenes = sorted(imagenes)

    if not imagenes:

        raise RuntimeError(
            "No hay imágenes dentro de assets/gta6."
        )

    print(
        f"Imágenes encontradas: {len(imagenes)}"
    )

    return imagenes


# =====================================
# PREPARAR IMAGEN SIN CORTARLA
# =====================================

def preparar_imagen(ruta, destino):

    with Image.open(ruta) as original:

        imagen = ImageOps.exif_transpose(
            original
        ).convert("RGB")

        fondo = ImageOps.fit(
            imagen,
            (ANCHO, ALTO),
            method=Image.Resampling.LANCZOS
        )

        fondo = fondo.filter(
            ImageFilter.GaussianBlur(30)
        )

        fondo = ImageEnhance.Brightness(
            fondo
        ).enhance(0.38)

        principal = ImageOps.contain(
            imagen,
            (1000, 1550),
            method=Image.Resampling.LANCZOS
        )

        x = (ANCHO - principal.width) // 2
        y = (ALTO - principal.height) // 2

        panel = Image.new(
            "RGBA",
            (
                principal.width + 24,
                principal.height + 24
            ),
            (0, 0, 0, 170)
        )

        fondo_rgba = fondo.convert("RGBA")

        fondo_rgba.alpha_composite(
            panel,
            (x - 12, y - 12)
        )

        fondo_rgba.paste(
            principal,
            (x, y)
        )

        fondo_final = fondo_rgba.convert("RGB")

        fondo_final.save(
            destino,
            quality=95
        )


def preparar_todas_las_imagenes():

    imagenes = buscar_imagenes()

    if CARPETA_PROCESADAS.exists():

        shutil.rmtree(
            CARPETA_PROCESADAS
        )

    CARPETA_PROCESADAS.mkdir(
        parents=True,
        exist_ok=True
    )

    procesadas = []

    for numero, imagen in enumerate(
        imagenes,
        start=1
    ):

        destino = (
            CARPETA_PROCESADAS /
            f"imagen_{numero:03}.jpg"
        )

        print(
            f"Preparando imagen {numero}/{len(imagenes)}: "
            f"{imagen.name}"
        )

        preparar_imagen(
            imagen,
            destino
        )

        procesadas.append(destino)

    return procesadas


# =====================================
# CREAR FONDO DEL VIDEO
# =====================================

def preparar_fondo(duracion):

    imagenes = preparar_todas_las_imagenes()

    tiempo_por_imagen = (
        duracion / len(imagenes)
    )

    clips = []

    for imagen in imagenes:

        clip = (
            ImageClip(str(imagen))
            .with_duration(tiempo_por_imagen)
        )

        clips.append(clip)

    fondo = concatenate_videoclips(
        clips,
        method="compose"
    )

    return fondo, clips


# =====================================
# CREAR TEXTO
# =====================================

def crear_texto(
    texto,
    tamano,
    color,
    ancho,
    alto
):

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
# CREAR VIDEO
# =====================================

def crear_video(
    titulo,
    gancho,
    narracion
):

    palabras = generar_voz(narracion)

    audio = AudioFileClip("voz.mp3")

    duracion = audio.duration

    fondo, clips_imagenes = preparar_fondo(
        duracion
    )

    capas = [fondo]

    # TITULO INICIAL

    texto_titulo = crear_texto(
        titulo[:100],
        64,
        "yellow",
        960,
        280
    )

    texto_titulo = (
        texto_titulo
        .with_duration(
            min(3.5, duracion)
        )
        .with_position(
            ("center", 170)
        )
    )

    capas.append(texto_titulo)

    # GANCHO

    if gancho:

        texto_gancho = crear_texto(
            gancho[:120],
            46,
            "white",
            940,
            220
        )

        texto_gancho = (
            texto_gancho
            .with_duration(
                min(2.7, duracion)
            )
            .with_position(
                ("center", 530)
            )
        )

        capas.append(texto_gancho)

    # SUBTITULOS SINCRONIZADOS

    grupos = agrupar_palabras(
        palabras,
        duracion
    )

    guardar_subtitulos(grupos)

    for grupo in grupos:

        subtitulo = crear_texto(
            grupo["texto"],
            52,
            "white",
            960,
            190
        )

        inicio = max(
            0,
            grupo["inicio"] - 0.02
        )

        final = min(
            duracion,
            grupo["final"] + 0.12
        )

        tiempo = max(
            0.1,
            final - inicio
        )

        subtitulo = (
            subtitulo
            .with_start(inicio)
            .with_duration(tiempo)
            .with_position(
                ("center", 1400)
            )
        )

        capas.append(subtitulo)

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
        .with_position(
            ("center", 1815)
        )
    )

    capas.append(marca)

    # MONTAR VIDEO

    print("Montando vídeo vertical...")

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
        fps=30,
        codec="libx264",
        audio_codec="aac",
        preset="ultrafast",
        threads=2
    )

    video_final.close()
    fondo.close()
    audio.close()

    for clip in clips_imagenes:
        clip.close()

    print(
        "Vídeo terminado correctamente."
    )


# =====================================
# PUBLICACION
# =====================================

def guardar_publicacion(
    descripcion,
    hashtags
):

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

    (
        titulo,
        gancho,
        narracion,
        descripcion,
        hashtags
    ) = generar_guion()

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
