"""Puntos de entrada para la automatización (n8n).

Son dos rutas y hacen lo mínimo: entregar el informe y registrar que se
despachó. No se expone nada más, y en particular no se expone ninguna ruta que
permita modificar un registro de terreno: la inmutabilidad vale también para
los sistemas que se conectan desde afuera, no sólo para las personas.

La autenticación es un token compartido en la cabecera `X-SIG-Token`. Es
suficiente para una integración entre dos servicios de la misma red, y se
documenta como tal: para exposición a internet correspondería OAuth, que está
fuera del alcance de esta entrega.
"""

import hmac
import logging
from functools import wraps

from django.conf import settings
from django.http import FileResponse, Http404, JsonResponse
from django.shortcuts import get_object_or_404
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET, require_POST

from .models import InformeVisita

log = logging.getLogger(__name__)


def requiere_token(vista):
    """Comparación en tiempo constante, para no filtrar el token por timing."""

    @wraps(vista)
    def envoltura(request, *args, **kwargs):
        esperado = getattr(settings, "SIG_API_TOKEN", "")
        recibido = request.headers.get("X-SIG-Token", "")
        if not esperado or not hmac.compare_digest(esperado, recibido):
            log.warning("Petición a la API rechazada desde %s", request.META.get("REMOTE_ADDR"))
            return JsonResponse({"error": "Token inválido o ausente."}, status=401)
        return vista(request, *args, **kwargs)

    return envoltura


@require_GET
@requiere_token
def informe_pdf(request, pk):
    """Entrega el PDF archivado para que la automatización lo adjunte."""
    informe = get_object_or_404(InformeVisita, pk=pk)
    try:
        archivo = informe.archivo.open("rb")
    except FileNotFoundError:
        raise Http404("El archivo del informe no está disponible.")
    respuesta = FileResponse(
        archivo,
        as_attachment=True,
        filename=informe.archivo.name.split("/")[-1],
        content_type="application/pdf",
    )
    # Permite a la automatización verificar que recibió el archivo correcto.
    respuesta["X-SIG-Hash"] = informe.hash_sha256
    return respuesta


@csrf_exempt
@require_POST
@requiere_token
def informe_despacho(request, pk):
    """Registra que el informe fue despachado al cliente.

    No altera el documento ni su huella: sólo añade a quién y cuándo se envió,
    que es el único dato que un informe admite después de generado.
    """
    informe = get_object_or_404(InformeVisita, pk=pk)
    destinatario = (request.POST.get("destinatario") or "").strip()
    if not destinatario:
        import json
        try:
            destinatario = (json.loads(request.body or b"{}").get("destinatario") or "").strip()
        except ValueError:
            destinatario = ""
    if not destinatario:
        return JsonResponse({"error": "Falta el destinatario."}, status=400)

    informe.marcar_despachado(destinatario)
    informe.refresh_from_db()
    log.info("Informe %s despachado a %s por la automatización.", informe.pk, destinatario)
    return JsonResponse({
        "ok": True,
        "informe": informe.pk,
        "version": informe.version,
        "destinatario": informe.destinatario,
        "ts_despacho": informe.ts_despacho.isoformat(),
        "hash_sha256": informe.hash_sha256,
    })
