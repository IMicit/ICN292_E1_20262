"""Vistas del SIG IMELSE.

El control de acceso vive en los decoradores `solo_roles`: cada vista declara
qué perfiles pueden entrar (RNF-05). La inmutabilidad no se defiende aquí sino
en los modelos, de modo que ninguna vista pueda saltársela por descuido.
"""

from functools import wraps

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.exceptions import ValidationError
from django.db.models import Count, Max, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from django.http import FileResponse, Http404

from .forms import (
    EvidenciaForm,
    HallazgoForm,
    MaterialFaltanteForm,
    MedicionForm,
    ObservacionForm,
    PendienteForm,
)
from django.db import connection

from .consultas import ejecutar, leer_consultas
from .informes import generar_informe
from .integraciones import avisar_visita_cerrada
from .libro_anual import actualizar_libro
from .models import (
    Ciclo,
    LibroAnual,
    Evidencia,
    InformeVisita,
    ItemChecklist,
    Local,
    MaterialFaltante,
    Observacion,
    Pendiente,
    RegistroItem,
    RegistroTablero,
    Tablero,
    Usuario,
    Visita,
)


# ---------------------------------------------------------------------------
# Control de acceso por perfil (RF-14, RNF-05)
# ---------------------------------------------------------------------------

def solo_roles(*roles):
    def decorador(vista):
        @wraps(vista)
        @login_required
        def envoltura(request, *args, **kwargs):
            if request.user.rol not in roles:
                messages.error(
                    request, "Su perfil no tiene acceso a esta sección."
                )
                return redirect("inicio")
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador


TECNICO = Usuario.Rol.TECNICO
ADMIN = Usuario.Rol.ADMINISTRACION
GERENCIA = Usuario.Rol.GERENCIA


# ---------------------------------------------------------------------------
# Entrada
# ---------------------------------------------------------------------------

@login_required
def inicio(request):
    if request.user.es_tecnico:
        return redirect("visitas")
    return redirect("panel")


# ---------------------------------------------------------------------------
# Terreno — flujo del técnico
# ---------------------------------------------------------------------------

@solo_roles(TECNICO, ADMIN, GERENCIA)
def visitas(request):
    qs = Visita.objects.select_related("local", "ciclo").prefetch_related("cuadrilla")
    if request.user.es_tecnico:
        qs = qs.filter(cuadrilla=request.user)
    return render(request, "core/visitas.html", {"visitas": qs})


@solo_roles(TECNICO, ADMIN, GERENCIA)
def visita_detalle(request, pk):
    visita = get_object_or_404(
        Visita.objects.select_related("local", "ciclo"), pk=pk
    )
    registrados = visita.tableros_registrados_ids()
    pendientes = {p.tablero_id: p for p in visita.pendientes.select_related("tablero")}

    filas = []
    for tablero in visita.tableros_esperados():
        if tablero.id in registrados:
            estado = "registrado"
        elif tablero.id in pendientes:
            estado = "pendiente"
        else:
            estado = "sin_registro"
        filas.append({"tablero": tablero, "estado": estado,
                      "pendiente": pendientes.get(tablero.id)})

    # Ítems de la pauta cuyo ámbito es la visita completa (no el tablero).
    vigentes = {}
    for r in (
        visita.items.filter(registro_tablero__isnull=True)
        .select_related("item", "usuario")
        .order_by("ts_captura", "id")
    ):
        vigentes[r.item_id] = r  # el último que llega es el vigente

    items_visita = [
        {"item": item, "respuesta": vigentes.get(item.id)}
        for item in ItemChecklist.objects.filter(
            ambito=ItemChecklist.Ambito.VISITA
        ).select_related("seccion")
    ]

    return render(
        request,
        "core/visita_detalle.html",
        {
            "visita": visita,
            "filas": filas,
            "items_visita": items_visita,
            "sin_resolver": visita.tableros_sin_resolver().count(),
            "resultados": RegistroItem.Resultado.choices,
            "puede_editar": request.user.es_tecnico
            and visita.estado != Visita.Estado.CERRADA,
        },
    )


@solo_roles(TECNICO)
def visita_items(request, pk):
    """Guarda los ítems de la pauta de ámbito visita (secciones 1, 2 parcial y 5)."""
    visita = get_object_or_404(Visita, pk=pk)
    if visita.estado == Visita.Estado.CERRADA:
        messages.error(request, "La visita está cerrada: no admite registros nuevos.")
        return redirect("visita_detalle", pk=pk)

    _guardar_respuestas(
        request,
        visita=visita,
        registro_tablero=None,
        items=ItemChecklist.objects.filter(ambito=ItemChecklist.Ambito.VISITA),
    )
    if visita.estado == Visita.Estado.PLANIFICADA:
        visita.estado = Visita.Estado.EN_EJECUCION
        visita.save(update_fields=["estado"])
    messages.success(request, "Respuestas registradas.")
    return redirect("visita_detalle", pk=pk)


def _guardar_respuestas(request, visita, registro_tablero, items):
    """Crea un RegistroItem por cada respuesta nueva o distinta de la vigente.

    Nunca actualiza una fila existente: si la respuesta cambia, encadena la
    nueva a la anterior mediante `corrige_a` (RNF-02).
    """
    creados, sin_justificar = 0, []
    for item in items:
        valor = request.POST.get(f"item_{item.id}")
        if valor not in dict(RegistroItem.Resultado.choices):
            continue
        justificacion = (request.POST.get(f"just_{item.id}") or "").strip()

        # Simetría de la regla: no se declara hecho sin foto (RF-03, al sellar),
        # y no se declara no hecho sin decir por qué. El casillero mudo del
        # papel no tiene equivalente en el sistema.
        if valor in (RegistroItem.Resultado.NO, RegistroItem.Resultado.NA) and not justificacion:
            sin_justificar.append(item)
            continue

        anterior = (
            RegistroItem.objects.filter(
                visita=visita, registro_tablero=registro_tablero, item=item
            )
            .order_by("-ts_captura", "-id")
            .first()
        )
        if anterior and anterior.resultado == valor and anterior.justificacion == justificacion:
            continue
        RegistroItem.objects.create(
            visita=visita,
            registro_tablero=registro_tablero,
            item=item,
            resultado=valor,
            justificacion=justificacion,
            usuario=request.user,
            ts_captura=timezone.now(),
            corrige_a=anterior,
        )
        creados += 1

    if sin_justificar:
        messages.error(
            request,
            f"{len(sin_justificar)} ítem(s) marcados «No» o «No aplica» quedaron sin "
            "registrar: hay que indicar el motivo.",
        )
    return creados


@solo_roles(TECNICO, ADMIN, GERENCIA)
def tablero_registro(request, visita_pk, tablero_pk):
    visita = get_object_or_404(Visita, pk=visita_pk)
    tablero = get_object_or_404(Tablero, pk=tablero_pk, local=visita.local)

    registro = (
        RegistroTablero.objects.filter(visita=visita, tablero=tablero)
        .order_by("-ts_inicio")
        .first()
    )
    editable = request.user.es_tecnico and visita.estado != Visita.Estado.CERRADA

    if registro is None:
        if not editable:
            messages.info(request, "Este tablero todavía no tiene registro.")
            return redirect("visita_detalle", pk=visita.pk)
        registro = RegistroTablero.objects.create(
            visita=visita, tablero=tablero, usuario=request.user
        )
        if visita.estado == Visita.Estado.PLANIFICADA:
            visita.estado = Visita.Estado.EN_EJECUCION
            visita.save(update_fields=["estado"])

    items = ItemChecklist.objects.filter(
        ambito=ItemChecklist.Ambito.TABLERO
    ).select_related("seccion")

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "guardar" and editable and not registro.cerrado:
            n = _guardar_respuestas(request, visita, registro, items)
            messages.success(request, f"{n} respuesta(s) registrada(s).")
            return redirect("tablero_registro", visita_pk=visita.pk, tablero_pk=tablero.pk)

        if accion == "foto" and editable and not registro.cerrado:
            form_foto = EvidenciaForm(request.POST, request.FILES, items=items)
            if form_foto.is_valid():
                evidencia = form_foto.guardar(registro, request.user)
                messages.success(
                    request,
                    f"Fotografía registrada y sellada con fecha y hora · "
                    f"{evidencia.bytes // 1024} KB · respalda "
                    f"{evidencia.items.count()} ítem(s) · hash {evidencia.hash_corto}",
                )
                return redirect(
                    "tablero_registro", visita_pk=visita.pk, tablero_pk=tablero.pk
                )
            for errores in form_foto.errors.values():
                for e in errores:
                    messages.error(request, e)

        elif accion == "medicion" and editable and not registro.cerrado:
            form_med = MedicionForm(request.POST)
            if form_med.is_valid():
                medicion = form_med.save(commit=False)
                medicion.registro_tablero = registro
                medicion.usuario = request.user
                medicion.ts = timezone.now()
                medicion.save()
                avisos = medicion.anomalias()
                if avisos:
                    messages.warning(
                        request,
                        "Mediciones registradas, con lecturas fuera de rango: "
                        + "; ".join(avisos),
                    )
                else:
                    messages.success(request, "Mediciones eléctricas registradas.")
                return redirect(
                    "tablero_registro", visita_pk=visita.pk, tablero_pk=tablero.pk
                )
            messages.error(request, "Revise los valores de la hoja de mediciones.")

        elif accion == "observacion":
            form = ObservacionForm(request.POST)
            if form.is_valid():
                obs = form.save(commit=False)
                obs.registro_tablero = registro
                obs.autor = request.user
                obs.ts = timezone.now()
                obs.save()
                messages.success(request, "Observación anexada. El registro original no cambió.")
                return redirect(
                    "tablero_registro", visita_pk=visita.pk, tablero_pk=tablero.pk
                )

        elif accion == "hallazgo" and editable:
            form = HallazgoForm(request.POST)
            if form.is_valid():
                hallazgo = form.save(commit=False)
                hallazgo.registro_tablero = registro
                hallazgo.usuario = request.user
                hallazgo.ts = timezone.now()
                hallazgo.save()
                messages.success(request, "Hallazgo registrado.")
                return redirect(
                    "tablero_registro", visita_pk=visita.pk, tablero_pk=tablero.pk
                )

        elif accion == "cerrar" and editable and not registro.cerrado:
            try:
                registro.sellar()
            except ValidationError as e:
                messages.error(request, "; ".join(e.messages))
            else:
                messages.success(
                    request,
                    f"Tablero {tablero.codigo} cerrado. El registro quedó sellado.",
                )
                return redirect("visita_detalle", pk=visita.pk)

    # Respuesta vigente y cadena de correcciones por ítem.
    cadenas = {}
    for r in registro.items.select_related("item", "usuario", "corrige_a").order_by(
        "ts_captura", "id"
    ):
        cadenas.setdefault(r.item_id, []).append(r)

    # Qué ítems ya tienen fotografía vinculada (RF-03).
    con_foto = set()
    for ev in registro.evidencias.prefetch_related("items"):
        con_foto.update(ev.items.values_list("id", flat=True))

    filas_pauta = [
        {
            "item": item,
            "respuesta": cadenas.get(item.id, [None])[-1],
            "historial": cadenas.get(item.id, [])[:-1],
            "con_foto": item.id in con_foto,
        }
        for item in items
    ]

    medicion = getattr(registro, "medicion", None)

    return render(
        request,
        "core/tablero_registro.html",
        {
            "visita": visita,
            "tablero": tablero,
            "registro": registro,
            "filas_pauta": filas_pauta,
            "evidencias": registro.evidencias.prefetch_related("items").select_related("usuario"),
            "observaciones": registro.observaciones.select_related("autor"),
            "hallazgos": registro.hallazgos.select_related("usuario"),
            "medicion": medicion,
            "form_evidencia": EvidenciaForm(items=items),
            "form_observacion": ObservacionForm(),
            "form_hallazgo": HallazgoForm(),
            "form_medicion": MedicionForm() if medicion is None else None,
            "editable": editable and not registro.cerrado,
            "faltantes": registro.items_faltantes() if not registro.cerrado else [],
            "sin_evidencia": registro.items_sin_evidencia() if not registro.cerrado else [],
            "resultados": RegistroItem.Resultado.choices,
        },
    )


@solo_roles(TECNICO)
def declarar_pendiente(request, visita_pk, tablero_pk):
    """RF-07: única salida legítima para no intervenir un tablero."""
    visita = get_object_or_404(Visita, pk=visita_pk)
    tablero = get_object_or_404(Tablero, pk=tablero_pk, local=visita.local)

    if visita.estado == Visita.Estado.CERRADA:
        messages.error(request, "La visita está cerrada.")
        return redirect("visita_detalle", pk=visita.pk)

    if request.method == "POST":
        form = PendienteForm(request.POST)
        if form.is_valid():
            pendiente = form.save(commit=False)
            pendiente.visita = visita
            pendiente.tablero = tablero
            pendiente.usuario = request.user
            pendiente.save()
            messages.success(
                request, f"Tablero {tablero.codigo} declarado pendiente."
            )
            return redirect("visita_detalle", pk=visita.pk)
    else:
        form = PendienteForm()

    return render(
        request,
        "core/pendiente.html",
        {"visita": visita, "tablero": tablero, "form": form},
    )


@solo_roles(TECNICO)
def cerrar_visita(request, pk):
    """RF-06 + RF-08: el cierre valida cobertura y publica la evidencia a oficina."""
    visita = get_object_or_404(Visita, pk=pk)
    if request.method == "POST":
        try:
            visita.cerrar(request.user)
        except ValidationError as e:
            messages.error(request, "; ".join(e.messages))
        else:
            # RF-13: el informe se genera y archiva en el acto. El documento que
            # va al cliente es un objeto del sistema, no un archivo que alguien
            # compone a mano después.
            informe = generar_informe(visita, request.user)
            # El libro anual es una vista derivada: se rehace para que la
            # planilla de gerencia nunca quede atrasada respecto del sistema.
            actualizar_libro(visita.fecha.year, request.user)
            # RF-13 completo: el hecho se anuncia y la automatización despacha.
            # Si n8n no responde, el cierre ya ocurrió y no se deshace.
            aviso = avisar_visita_cerrada(visita, informe, request)
            messages.success(
                request,
                "Visita cerrada. La evidencia quedó disponible para la oficina en "
                "este mismo instante (RF-08), el informe v"
                f"{informe.version} se generó y archivó "
                f"({informe.bytes // 1024} KB, hash {informe.hash_corto}) y la "
                f"planilla anual {visita.fecha.year} se actualizó sola."
                + (" El despacho quedó en manos de la automatización."
                   if aviso else ""),
            )
    return redirect("visita_detalle", pk=pk)


# ---------------------------------------------------------------------------
# Oficina — administración y gerencia
# ---------------------------------------------------------------------------

def _latencia_minutos(visita):
    """Minutos entre el último tablero sellado en terreno y el cierre de la visita.

    Es exactamente la definición de `db/consultas/03-latencia-del-registro.sql`,
    y lo es a propósito: si el panel y la consulta calcularan la latencia de
    maneras distintas, uno de los dos estaría mintiendo y no habría forma de
    saber cuál.
    """
    if visita.estado != Visita.Estado.CERRADA or not visita.ts_cierre:
        return None
    ultimo = visita.registros_tablero.filter(cerrado=True).aggregate(u=Max("ts_cierre"))["u"]
    if not ultimo:
        return None
    return (visita.ts_cierre - ultimo).total_seconds() / 60.0


def _promedio(valores):
    """Promedio, y no mediana, a propósito.

    `docs/04-sql-consultas.md` y el informe publican la latencia como promedio.
    Si el panel mostrara la mediana, el sistema tendría dos números distintos
    para lo mismo (7,0 y 6,8 sobre los datos de demostración) y nadie podría
    decir cuál es el correcto. Un indicador se define una vez.
    """
    datos = [v for v in valores if v is not None]
    return sum(datos) / len(datos) if datos else None


@solo_roles(ADMIN, GERENCIA)
def panel(request):
    """RF-12: cobertura de tableros y visitas completas por local y por ciclo."""
    ciclo_id = request.GET.get("ciclo")
    ciclos = Ciclo.objects.all()
    ciclo = ciclos.filter(pk=ciclo_id).first() or ciclos.first()

    filas, tot_esperados, tot_registrados, completas = [], 0, 0, 0
    criticos = 0
    latencias = []
    visitas_ciclo = (
        Visita.objects.filter(ciclo=ciclo).select_related("local") if ciclo else []
    )
    for visita in visitas_ciclo:
        esperados = visita.total_tableros
        registrados = visita.total_registrados
        pendientes = visita.pendientes.count()
        tot_esperados += esperados
        tot_registrados += registrados
        criticos += visita.pendientes.filter(motivo__in=Pendiente.MOTIVOS_CRITICOS).count()
        latencias.append(_latencia_minutos(visita))
        if esperados and registrados == esperados:
            completas += 1
        filas.append(
            {
                "visita": visita,
                "esperados": esperados,
                "registrados": registrados,
                "pendientes": pendientes,
                "cobertura": visita.porcentaje_cobertura,
                "latencia": _latencia_minutos(visita),
            }
        )

    total_visitas = len(filas)
    latencia_promedio = _promedio(latencias)
    return render(
        request,
        "core/panel.html",
        {
            "ciclos": ciclos,
            "ciclo": ciclo,
            "filas": filas,
            "cobertura_global": round(100 * tot_registrados / tot_esperados)
            if tot_esperados
            else 0,
            "visitas_completas": completas,
            "total_visitas": total_visitas,
            "pct_completas": round(100 * completas / total_visitas) if total_visitas else 0,
            "latencia_promedio": round(latencia_promedio, 1) if latencia_promedio else None,
            "latencia_n": sum(1 for v in latencias if v is not None),
            "pendientes_criticos": criticos,
        },
    )


# ---------------------------------------------------------------------------
# Planificación del ciclo (RF-02)
# ---------------------------------------------------------------------------

@solo_roles(ADMIN, GERENCIA)
def ciclos(request):
    """RF-02: generar las visitas del ciclo a partir del calendario del contrato.

    Antes de esto las visitas se creaban a mano desde el administrador de
    Django, que es una herramienta de desarrollo y no de operación. El
    requisito está priorizado como *Must* y la manifestación que ataca es la
    P1, el traspaso diferido de información: una visita que nadie planificó es
    una visita que nadie echa de menos cuando no ocurre.
    """
    if request.method == "POST":
        ciclo = get_object_or_404(Ciclo, pk=request.POST.get("ciclo"))
        creadas = ciclo.generar_visitas()
        if creadas:
            messages.success(
                request,
                f"Se generaron {len(creadas)} visita(s) planificada(s) para el "
                f"{ciclo}, repartidas dentro de la ventana del ciclo.",
            )
        else:
            messages.info(
                request,
                f"El {ciclo} ya tiene visita en todos los locales del contrato. "
                "No se creó ni se modificó nada.",
            )
        return redirect("ciclos")

    filas = []
    for ciclo in Ciclo.objects.all():
        visitas = list(ciclo.visitas.select_related("local").all())
        faltantes = ciclo.locales_sin_visita()
        filas.append(
            {
                "ciclo": ciclo,
                "visitas": visitas,
                "n_visitas": len(visitas),
                "faltantes": faltantes,
                "n_faltantes": len(faltantes),
                "cerradas": sum(1 for v in visitas if v.estado == Visita.Estado.CERRADA),
            }
        )
    return render(
        request,
        "core/ciclos.html",
        {"filas": filas, "n_locales": Local.objects.count()},
    )


# ---------------------------------------------------------------------------
# Abastecimiento (RF-11)
# ---------------------------------------------------------------------------

@solo_roles(TECNICO)
def visita_materiales(request, pk):
    """RF-11: el técnico declara en terreno lo que faltó, durante la visita."""
    visita = get_object_or_404(Visita.objects.select_related("local"), pk=pk)
    if visita.estado == Visita.Estado.CERRADA:
        messages.error(
            request,
            "La visita está cerrada: no se pueden agregar materiales faltantes "
            "a un registro sellado (RNF-02).",
        )
        return redirect("visita_detalle", pk=visita.pk)

    if request.method == "POST":
        formulario = MaterialFaltanteForm(request.POST, visita=visita)
        if formulario.is_valid():
            material = formulario.save(commit=False)
            material.visita = visita
            material.usuario = request.user
            material.save()
            messages.success(request, "Material faltante registrado.")
            return redirect("visita_materiales", pk=visita.pk)
    else:
        formulario = MaterialFaltanteForm(visita=visita)

    return render(
        request,
        "core/materiales_visita.html",
        {
            "visita": visita,
            "formulario": formulario,
            "materiales": visita.materiales_faltantes.select_related("tablero", "usuario"),
        },
    )


@solo_roles(ADMIN, GERENCIA)
def materiales(request):
    """RF-11, lado oficina: qué hay que comprar, agrupado por local.

    Esta pantalla es la que ataca la manifestación P6. El registro en terreno
    por sí solo no evita el re-trabajo: lo evita que abastecimiento pueda ver
    la lista completa antes de la siguiente visita, con el local y el tablero
    que la están esperando.
    """
    consulta = MaterialFaltante.objects.select_related(
        "visita", "visita__local", "visita__ciclo", "tablero", "usuario"
    )
    solo_bloqueantes = request.GET.get("bloqueantes") == "1"
    if solo_bloqueantes:
        consulta = consulta.filter(urgencia=MaterialFaltante.Urgencia.BLOQUEA)

    por_local = {}
    for material in consulta:
        por_local.setdefault(material.visita.local, []).append(material)

    grupos = [
        {
            "local": local,
            "materiales": items,
            "bloqueantes": sum(1 for m in items if m.bloqueante),
        }
        for local, items in sorted(por_local.items(), key=lambda par: par[0].nombre)
    ]
    return render(
        request,
        "core/materiales.html",
        {
            "grupos": grupos,
            "total": sum(len(g["materiales"]) for g in grupos),
            "total_bloqueantes": sum(g["bloqueantes"] for g in grupos),
            "solo_bloqueantes": solo_bloqueantes,
        },
    )


@solo_roles(ADMIN, GERENCIA)
def informe_visita(request, pk):
    """RF-13: informe consolidado con la evidencia, listo para enviar al cliente."""
    visita = get_object_or_404(
        Visita.objects.select_related("local", "local__cliente", "ciclo"), pk=pk
    )
    registros = (
        visita.registros_tablero.select_related("tablero", "usuario")
        .prefetch_related("evidencias", "observaciones__autor", "hallazgos", "items__item__seccion")
        .order_by("tablero__codigo")
    )
    items_visita = [
        r for r in visita.items.filter(registro_tablero__isnull=True)
        .select_related("item", "item__seccion", "usuario") if r.vigente
    ]
    return render(
        request,
        "core/informe.html",
        {
            "visita": visita,
            "registros": registros,
            "items_visita": items_visita,
            "pendientes": visita.pendientes.select_related("tablero", "usuario"),
        },
    )


@solo_roles(ADMIN, GERENCIA, TECNICO)
def historial_tablero(request, pk):
    """RF-09: historial completo de intervenciones de un tablero, cronológico."""
    tablero = get_object_or_404(
        Tablero.objects.select_related("local", "local__cliente"), pk=pk
    )
    registros = (
        tablero.registros.select_related("visita", "visita__ciclo", "usuario")
        .prefetch_related("evidencias", "hallazgos", "observaciones__autor")
        .order_by("-ts_inicio")
    )
    return render(
        request,
        "core/historial.html",
        {"tablero": tablero, "registros": registros,
         "pendientes": tablero.pendientes.select_related("visita")},
    )


@solo_roles(ADMIN, GERENCIA)
def locales(request):
    qs = Local.objects.select_related("cliente").annotate(
        n_tableros=Count("tableros", filter=Q(tableros__activo=True))
    )
    return render(request, "core/locales.html", {"locales": qs})


# ---------------------------------------------------------------------------
# Informe despachable (RF-13)
# ---------------------------------------------------------------------------

@solo_roles(ADMIN, GERENCIA)
def informes_visita(request, pk):
    """Lista las versiones archivadas del informe y permite regenerar o despachar."""
    visita = get_object_or_404(
        Visita.objects.select_related("local", "local__cliente", "ciclo"), pk=pk
    )

    if request.method == "POST":
        accion = request.POST.get("accion")

        if accion == "generar":
            if visita.estado != Visita.Estado.CERRADA:
                messages.error(
                    request,
                    "El informe se emite sobre una visita cerrada: mientras la visita "
                    "sigue abierta, lo que se despacharía podría cambiar después.",
                )
            else:
                informe = generar_informe(visita, request.user)
                messages.success(
                    request,
                    f"Informe v{informe.version} generado y archivado "
                    f"({informe.bytes // 1024} KB, hash {informe.hash_corto}). "
                    "Las versiones anteriores se conservan.",
                )
            return redirect("informes_visita", pk=pk)

        if accion == "despachar":
            informe = get_object_or_404(
                InformeVisita, pk=request.POST.get("informe"), visita=visita
            )
            destinatario = (request.POST.get("destinatario") or "").strip()
            if not destinatario:
                messages.error(request, "Indique el correo del destinatario.")
            else:
                informe.marcar_despachado(destinatario)
                messages.success(
                    request,
                    f"Informe v{informe.version} marcado como despachado a "
                    f"{destinatario}. El documento y su hash no cambiaron.",
                )
            return redirect("informes_visita", pk=pk)

    return render(
        request,
        "core/informes.html",
        {
            "visita": visita,
            "informes": visita.informes.select_related("generado_por"),
            "destinatario_sugerido": "contacto@cliente-demo.cl",
        },
    )


@solo_roles(ADMIN, GERENCIA)
def descargar_informe(request, pk):
    """Entrega el PDF archivado. El archivo servido es el mismo que se hashea."""
    informe = get_object_or_404(InformeVisita.objects.select_related("visita"), pk=pk)
    try:
        archivo = informe.archivo.open("rb")
    except FileNotFoundError:
        raise Http404("El archivo del informe no está disponible.")
    return FileResponse(
        archivo, as_attachment=True, filename=informe.archivo.name.split("/")[-1]
    )


# ---------------------------------------------------------------------------
# Soporte de la operación sin conexión (RNF-01)
# ---------------------------------------------------------------------------

def service_worker(request):
    """Sirve el service worker desde la raíz del sitio.

    Un service worker sólo puede controlar rutas iguales o inferiores a su
    propia ruta, así que servirlo desde /static/ lo dejaría sin alcance sobre
    las pantallas de terreno.
    """
    from django.shortcuts import render as _render
    respuesta = _render(request, "core/sw.js", content_type="application/javascript")
    respuesta["Service-Worker-Allowed"] = "/"
    respuesta["Cache-Control"] = "no-cache"
    return respuesta


def manifiesto(request):
    """Permite instalar la aplicación en la pantalla de inicio del teléfono."""
    from django.http import JsonResponse
    return JsonResponse({
        "name": "SIG IMELSE — Mantención preventiva",
        "short_name": "SIG IMELSE",
        "start_url": "/visitas/",
        "display": "standalone",
        "background_color": "#f3f5f8",
        "theme_color": "#123a6b",
        "lang": "es-CL",
        "icons": [],
    })


# ---------------------------------------------------------------------------
# Libro anual de control (Excel con una hoja por mes)
# ---------------------------------------------------------------------------

@solo_roles(ADMIN, GERENCIA)
def libro_anual(request):
    """Planilla anual de control. Se rehace completa, nunca se parcha."""
    anios = sorted(
        Visita.objects.dates("fecha", "year", order="DESC"), reverse=True
    )
    anios = [d.year for d in anios] or [timezone.localdate().year]
    anio = int(request.GET.get("anio") or request.POST.get("anio") or anios[0])

    if request.method == "POST":
        libro = actualizar_libro(anio, request.user)
        messages.success(
            request,
            f"Planilla {anio} actualizada: {libro.n_visitas} visita(s), "
            f"{libro.bytes // 1024} KB. Refleja el estado del sistema en este momento.",
        )
        return redirect(f"{request.path}?anio={anio}")

    return render(
        request,
        "core/libro.html",
        {
            "anios": anios,
            "anio": anio,
            "libro": LibroAnual.objects.filter(anio=anio).first(),
            "meses": [
                "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio",
                "Julio", "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre",
            ],
        },
    )


@solo_roles(ADMIN, GERENCIA)
def descargar_libro(request, anio):
    libro = get_object_or_404(LibroAnual, anio=anio)
    if not libro.archivo:
        raise Http404("La planilla todavía no ha sido generada.")
    try:
        archivo = libro.archivo.open("rb")
    except FileNotFoundError:
        raise Http404("El archivo de la planilla no está disponible.")
    return FileResponse(
        archivo,
        as_attachment=True,
        filename=f"control-mantencion-{anio}.xlsx",
        content_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


# ---------------------------------------------------------------------------
# Consultas de negocio en SQL
# ---------------------------------------------------------------------------

@solo_roles(ADMIN, GERENCIA)
def consultas_sql(request):
    """Ejecuta las consultas de `db/consultas/` y muestra el resultado.

    Los archivos que se ejecutan aquí son los mismos que se entregan en el
    repositorio: no hay una copia dentro del código. Si el .sql cambia, cambia
    esta pantalla.
    """
    disponibles = leer_consultas()
    if not disponibles:
        return render(request, "core/consultas.html", {"consultas": []})

    slug = request.GET.get("q") or disponibles[0]["slug"]
    elegida = next((c for c in disponibles if c["slug"] == slug), disponibles[0])
    columnas, filas, error = ejecutar(elegida)

    return render(
        request,
        "core/consultas.html",
        {
            "consultas": disponibles,
            "elegida": elegida,
            "columnas": columnas,
            "filas": filas,
            "error": error,
            "motor": connection.vendor,
            "n_filas": len(filas),
        },
    )
