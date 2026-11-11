
def elegir_segmento(video):

    duracion = video.duration

    if duracion <= 0:
        raise ValueError("El vídeo no tiene duración válida.")

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

    # Calcular la escala necesaria para cubrir toda la pantalla.
    factor = max(
        ANCHO / segmento.w,
        ALTO / segmento.h
    )

    # Ampliar manteniendo las proporciones originales.
    segmento = segmento.resized(factor)

    # Recortar el centro para obtener exactamente 1080 x 1920.
    segmento = segmento.cropped(
        x_center=segmento.w / 2,
        y_center=segmento.h / 2,
        width=ANCHO,
        height=ALTO
    )

    print(
        f"Encuadre corregido: {segmento.w}x{segmento.h}"
    )

    return segmento
