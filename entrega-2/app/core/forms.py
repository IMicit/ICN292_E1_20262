"""Formularios del SIG IMELSE.

Aquí ocurren tres cosas que el enunciado del problema exige y que no son
cosméticas:

1. La compresión de la fotografía (RNF-08), para que el volumen declarado se
   cumpla aunque el teléfono envíe la imagen original de la cámara.
2. El estampado de fecha, hora, tablero y autor **dentro del píxel** de la
   imagen, de modo que el dato viaje con la fotografía aunque alguien la
   exporte fuera del sistema.
3. El rechazo de archivos que no provienen de una captura reciente, que es lo
   más cerca que un navegador permite estar de «no se puede subir de la galería».
"""

import io
from datetime import UTC, datetime, timedelta
from pathlib import Path

from django import forms
from django.conf import settings
from django.core.files.uploadedfile import InMemoryUploadedFile
from django.utils import timezone
from PIL import Image, ImageDraw, ImageFont, ImageOps

from .models import (
    Evidencia,
    Hallazgo,
    ItemChecklist,
    MaterialFaltante,
    MedicionElectrica,
    Observacion,
    Pendiente,
    RegistroItem,
)

FUENTES = Path(settings.BASE_DIR) / "core" / "static" / "core" / "fuentes"


def _fuente(nombre, tamano):
    try:
        return ImageFont.truetype(str(FUENTES / nombre), tamano)
    except OSError:
        return ImageFont.load_default()


def procesar_fotografia(imagen, pie, subpie):
    """Comprime la fotografía (RNF-08) y le estampa su procedencia.

    El sello se dibuja sobre el píxel, no como metadato: los metadatos EXIF se
    pierden al reenviar una imagen por mensajería o al exportarla, y el valor
    probatorio de la evidencia depende de que la fecha viaje con ella.
    """
    img = Image.open(imagen)
    img = ImageOps.exif_transpose(img)
    if img.mode not in ("RGB", "L"):
        img = img.convert("RGB")
    img = img.convert("RGB")
    img.thumbnail(
        (settings.EVIDENCIA_MAX_LADO_PX, settings.EVIDENCIA_MAX_LADO_PX),
        Image.LANCZOS,
    )

    ancho, alto = img.size
    escala = max(ancho, alto) / 1600
    cuerpo = max(14, int(26 * escala))
    pequena = max(11, int(19 * escala))
    margen = max(8, int(16 * escala))
    banda = cuerpo + pequena + margen * 2 + int(6 * escala)

    # Banda semitransparente al pie, para no tapar el contenido fotografiado.
    capa = Image.new("RGBA", (ancho, banda), (10, 20, 30, 205))
    img.paste(capa, (0, alto - banda), capa)

    dib = ImageDraw.Draw(img)
    dib.text((margen, alto - banda + margen), pie,
             fill=(255, 205, 80), font=_fuente("DejaVuSans-Bold.ttf", cuerpo))
    dib.text((margen, alto - banda + margen + cuerpo + int(5 * escala)), subpie,
             fill=(222, 232, 242), font=_fuente("DejaVuSans.ttf", pequena))

    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=settings.EVIDENCIA_CALIDAD_JPEG, optimize=True)
    buffer.seek(0)
    nombre = Path(imagen.name).stem[:40] + ".jpg"
    return InMemoryUploadedFile(
        buffer, "ImageField", nombre, "image/jpeg", buffer.getbuffer().nbytes, None
    )


class EvidenciaForm(forms.ModelForm):
    """Captura de evidencia vinculada a los ítems que respalda.

    `capture="environment"` hace que el navegador móvil abra la cámara trasera
    en lugar del selector de archivos. No es infalible —un usuario decidido
    puede sortearlo— y por eso se complementa con la validación de frescura del
    archivo que hace `clean_archivo`.
    """

    capturada_en = forms.CharField(widget=forms.HiddenInput(), required=False)

    class Meta:
        model = Evidencia
        fields = ["archivo", "items"]
        widgets = {
            "archivo": forms.ClearableFileInput(
                attrs={"accept": "image/*", "capture": "environment", "id": "campo-foto"}
            ),
            "items": forms.CheckboxSelectMultiple(),
        }
        labels = {
            "archivo": "Fotografía (se abre la cámara)",
            "items": "Ítems que esta fotografía respalda",
        }

    def __init__(self, *args, items=None, **kwargs):
        super().__init__(*args, **kwargs)
        if items is not None:
            self.fields["items"].queryset = items
        self.fields["items"].required = True
        self.fields["items"].help_text = (
            "Marque todos los ítems que la fotografía evidencia. Una captura "
            "del tablero abierto puede respaldar varios."
        )

    def clean_archivo(self):
        archivo = self.cleaned_data["archivo"]
        if archivo.content_type and not archivo.content_type.startswith("image/"):
            raise forms.ValidationError("El archivo debe ser una imagen.")
        return archivo

    def clean(self):
        datos = super().clean()
        marca = (datos.get("capturada_en") or "").strip()
        limite = getattr(settings, "EVIDENCIA_MAX_ANTIGUEDAD_S", 900)

        # Una fotografía tomada en un subterráneo sin señal puede subirse horas
        # después (RNF-01). Lo que se exige es que fuera reciente **cuando se
        # capturó**, no cuando por fin logró enviarse: sin este descuento, una
        # visita sincronizada al salir del local se rechazaría entera.
        desfase = (self.data.get("desfase_cola") or "0").strip()
        if desfase.isdigit():
            limite += int(desfase) / 1000

        if marca.isdigit():
            # `File.lastModified` del navegador, en milisegundos. El UTC viene
            # de la biblioteca estándar y no de `django.utils.timezone`, que
            # dejó de exponer `utc` en Django 5.0.
            tomada = datetime.fromtimestamp(int(marca) / 1000, tz=UTC)
            antiguedad = timezone.now() - tomada
            if antiguedad > timedelta(seconds=limite):
                self.add_error(
                    "archivo",
                    "Esta imagen es de hace "
                    f"{int(antiguedad.total_seconds() // 60)} minutos. La evidencia "
                    "debe capturarse en el momento: use la cámara, no la galería.",
                )
            elif antiguedad < timedelta(seconds=-120):
                self.add_error("archivo", "La fecha del archivo es futura. Revise el reloj del dispositivo.")
        return datos

    def guardar(self, registro, usuario):
        """Comprime, estampa y graba. Devuelve la evidencia ya con sus ítems."""
        ahora = timezone.localtime()
        tablero = registro.tablero
        archivo = procesar_fotografia(
            self.cleaned_data["archivo"],
            pie=f"{tablero.codigo} · {ahora:%d-%m-%Y %H:%M:%S}",
            subpie=(
                f"{tablero.local.nombre} · {usuario.get_full_name() or usuario.username} · "
                f"visita {registro.visita.fecha:%d-%m-%Y} · SIG IMELSE"
            ),
        )
        evidencia = Evidencia(
            registro_tablero=registro, archivo=archivo, usuario=usuario, ts=timezone.now()
        )
        evidencia.save()
        evidencia.items.set(self.cleaned_data["items"])
        return evidencia


class ObservacionForm(forms.ModelForm):
    class Meta:
        model = Observacion
        fields = ["texto"]
        widgets = {
            "texto": forms.Textarea(
                attrs={
                    "rows": 3,
                    "class": "campo",
                    "placeholder": "Qué se observa. No modifica lo registrado; queda anexado.",
                }
            )
        }
        labels = {"texto": "Observación"}


class PendienteForm(forms.ModelForm):
    class Meta:
        model = Pendiente
        fields = ["motivo", "comentario"]
        widgets = {
            "motivo": forms.Select(attrs={"class": "campo"}),
            "comentario": forms.Textarea(attrs={"rows": 3, "class": "campo"}),
        }
        labels = {"motivo": "Motivo", "comentario": "Detalle"}

    def clean(self):
        datos = super().clean()
        if datos.get("motivo") == Pendiente.Motivo.OTRO and not datos.get("comentario"):
            self.add_error("comentario", "Si el motivo es «Otro», el detalle es obligatorio.")
        return datos


class HallazgoForm(forms.ModelForm):
    class Meta:
        model = Hallazgo
        fields = ["criticidad", "descripcion"]
        widgets = {
            "criticidad": forms.Select(attrs={"class": "campo"}),
            "descripcion": forms.Textarea(attrs={"rows": 3, "class": "campo"}),
        }
        labels = {"criticidad": "Criticidad", "descripcion": "Descripción del hallazgo"}


class MaterialFaltanteForm(forms.ModelForm):
    """Material o repuesto que faltó en terreno (RF-11).

    El selector de tablero se limita a los tableros del local de la visita, y
    admite quedar vacío: un faltante puede ser de un tablero concreto o de
    consumo general del local. La lista completa del catálogo no tiene sentido
    acá, porque un técnico en un local no puede pedir material para otro.
    """

    def __init__(self, *args, visita=None, **kwargs):
        super().__init__(*args, **kwargs)
        if visita is not None:
            self.fields["tablero"].queryset = visita.local.tableros.filter(activo=True)
        self.fields["tablero"].empty_label = "Sin tablero específico (consumo del local)"
        self.fields["tablero"].required = False

    class Meta:
        model = MaterialFaltante
        fields = ["tablero", "descripcion", "cantidad", "unidad", "urgencia", "comentario"]
        widgets = {
            "tablero": forms.Select(attrs={"class": "campo"}),
            "descripcion": forms.TextInput(
                attrs={
                    "class": "campo",
                    "placeholder": "Automático diferencial 2x25A, curva C",
                    "autocomplete": "off",
                }
            ),
            "cantidad": forms.NumberInput(attrs={"class": "campo", "min": 1, "step": 1}),
            "unidad": forms.Select(attrs={"class": "campo"}),
            "urgencia": forms.Select(attrs={"class": "campo"}),
            "comentario": forms.Textarea(attrs={"rows": 2, "class": "campo"}),
        }
        labels = {
            "tablero": "Tablero",
            "descripcion": "Qué faltó",
            "cantidad": "Cantidad",
            "unidad": "Unidad",
            "urgencia": "Urgencia",
            "comentario": "Detalle (opcional)",
        }

    def clean_descripcion(self):
        texto = (self.cleaned_data.get("descripcion") or "").strip()
        if len(texto) < 5:
            raise forms.ValidationError(
                "Describa el material con el detalle suficiente para comprarlo: "
                "«repuesto» no alcanza para hacer una orden de compra."
            )
        return texto


class MedicionForm(forms.ModelForm):
    """Hoja de mediciones eléctricas N° 002214 (RF-17)."""

    class Meta:
        model = MedicionElectrica
        exclude = ["registro_tablero", "usuario", "ts"]
        widgets = {
            "observaciones": forms.Textarea(attrs={"rows": 3, "class": "campo"}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, campo in self.fields.items():
            if nombre == "observaciones":
                continue
            campo.widget.attrs.update(
                {"class": "campo", "inputmode": "decimal", "step": "0.01", "placeholder": "—"}
            )

    GRUPOS = [
        ("Tensión entre fases", ["v_l1_l2", "v_l2_l3", "v_l3_l1"]),
        ("Línea y neutro", ["v_l1_n", "v_l2_n", "v_l3_n"]),
        ("Línea y tierra", ["v_l1_t", "v_l2_t", "v_l3_t"]),
        ("Tierra y neutro", ["v_t_n"]),
        ("Corriente", ["i_l1", "i_l2", "i_l3"]),
        ("Factor de potencia", ["cos_fi"]),
    ]

    def grupos(self):
        for titulo, nombres in self.GRUPOS:
            yield titulo, [self[n] for n in nombres]
