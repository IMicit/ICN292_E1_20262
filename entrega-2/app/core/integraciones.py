"""Integración con la plataforma de automatización (n8n).

El sistema avisa hacia afuera cuando ocurre un hecho de negocio —aquí, el
cierre de una visita— y deja que la automatización decida qué hacer con eso.
Esa separación es deliberada: el SIG no sabe mandar correos ni le corresponde
saberlo. Su responsabilidad termina cuando el hecho queda registrado y
anunciado.

Regla de oro de este módulo: **si la automatización está caída, el cierre de la
visita se completa igual**. Un técnico en terreno no puede quedar bloqueado
porque un servidor de correo no responde.
"""

import json
import logging
import urllib.error
import urllib.request

from django.conf import settings
from django.urls import reverse

from .models import Pendiente

log = logging.getLogger(__name__)


def _url_absoluta(request, nombre, *args):
    ruta = reverse(nombre, args=args)
    if request is not None:
        return request.build_absolute_uri(ruta)
    return f"{settings.SIG_BASE_URL.rstrip('/')}{ruta}"


def avisar_visita_cerrada(visita, informe, request=None):
    """Notifica el cierre de una visita al webhook de n8n.

    Devuelve True si el aviso salió, False si no se pudo enviar. Nunca lanza
    una excepción hacia arriba: el cierre de la visita ya ocurrió y no se
    deshace porque falle un aviso.
    """
    destino = getattr(settings, "N8N_WEBHOOK_URL", "")
    if not destino:
        log.info("N8N_WEBHOOK_URL no configurado: no se envía aviso de cierre.")
        return False

    pendientes = list(
        visita.pendientes.select_related("tablero").all()
    )
    criticos = [p for p in pendientes if p.motivo in Pendiente.MOTIVOS_CRITICOS]

    carga = {
        "evento": "visita.cerrada",
        "visita": {
            "id": visita.pk,
            "fecha": visita.fecha.isoformat(),
            "ciclo": str(visita.ciclo),
            "local": visita.local.nombre,
            "comuna": visita.local.comuna,
            "cliente": visita.local.cliente.razon_social,
            "cerrada_por": visita.cerrada_por.get_full_name() if visita.cerrada_por else "",
            "ts_cierre": visita.ts_cierre.isoformat() if visita.ts_cierre else None,
        },
        "cobertura": {
            "tableros_esperados": visita.total_tableros,
            "tableros_registrados": visita.total_registrados,
            "porcentaje": visita.porcentaje_cobertura,
        },
        "pendientes": {
            "total": len(pendientes),
            "criticos": len(criticos),
            "detalle": [
                {
                    "tablero": p.tablero.codigo,
                    "ubicacion": p.tablero.ubicacion,
                    "motivo": p.get_motivo_display(),
                    "comentario": p.comentario,
                }
                for p in pendientes
            ],
        },
        "informe": {
            "id": informe.pk,
            "version": informe.version,
            "hash_sha256": informe.hash_sha256,
            "bytes": informe.bytes,
            "url_descarga": _url_absoluta(request, "api_informe_pdf", informe.pk),
            "url_despacho": _url_absoluta(request, "api_informe_despacho", informe.pk),
        },
        # El destinatario sale del catálogo, no lo escribe el técnico.
        "destinatario": getattr(settings, "SIG_CORREO_CLIENTE", ""),
        "destinatario_gerencia": getattr(settings, "SIG_CORREO_GERENCIA", ""),
    }

    cuerpo = json.dumps(carga).encode("utf-8")
    peticion = urllib.request.Request(
        destino,
        data=cuerpo,
        headers={
            "Content-Type": "application/json",
            "X-SIG-Token": getattr(settings, "SIG_API_TOKEN", ""),
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(peticion, timeout=5) as r:
            log.info("Aviso de cierre enviado a n8n (HTTP %s).", r.status)
            return True
    except (urllib.error.URLError, OSError, TimeoutError) as e:
        log.warning("No se pudo avisar a n8n del cierre de la visita %s: %s", visita.pk, e)
        return False
