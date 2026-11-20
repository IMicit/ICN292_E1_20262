"""
Modelo de datos del SIG de trazabilidad de mantención preventiva — IMELSE.

Regla transversal (RNF-02): los registros de ejecución son APPEND-ONLY.
Una vez creados no se modifican ni se eliminan. Una corrección es un registro
nuevo encadenado al original mediante `corrige_a`, con su propio autor y fecha.
La observación de un tercero (p. ej. el estudiante dual) es una entidad aparte
que comenta el registro sin alterarlo.
"""

import hashlib
from datetime import timedelta

from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import models
from django.utils import timezone


# ---------------------------------------------------------------------------
# Mixin de inmutabilidad
# ---------------------------------------------------------------------------

class AppendOnlyModel(models.Model):
    """Modelo que sólo admite inserciones. Implementa RNF-02 a nivel de ORM.

    No basta con esconder el botón de editar en la interfaz: la restricción
    vive en la capa de datos, de modo que ningún camino del código (vista,
    admin de Django o shell) pueda modificar o borrar un registro cerrado.
    """

    class Meta:
        abstract = True

    def save(self, *args, **kwargs):
        if self.pk is not None:
            raise PermissionDenied(
                f"{self.__class__.__name__} es un registro inmutable (RNF-02): "
                "no puede modificarse. Para corregirlo, cree un registro nuevo "
                "encadenado al original."
            )
        return super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        raise PermissionDenied(
            f"{self.__class__.__name__} es un registro inmutable (RNF-02): "
            "no puede eliminarse."
        )


# ---------------------------------------------------------------------------
# Usuarios y perfiles (RF-14, RNF-05)
# ---------------------------------------------------------------------------

class Usuario(AbstractUser):
    class Rol(models.TextChoices):
        TECNICO = "TECNICO", "Técnico"
        ADMINISTRACION = "ADMINISTRACION", "Administración"
        GERENCIA = "GERENCIA", "Gerencia"

    rol = models.CharField(max_length=20, choices=Rol.choices, default=Rol.TECNICO)

    class Meta(AbstractUser.Meta):
        db_table = "usuario"

    @property
    def es_tecnico(self):
        return self.rol == self.Rol.TECNICO

    @property
    def es_administracion(self):
        return self.rol == self.Rol.ADMINISTRACION

    @property
    def es_gerencia(self):
        return self.rol == self.Rol.GERENCIA

    def __str__(self):
        return f"{self.get_full_name() or self.username} ({self.get_rol_display()})"


# ---------------------------------------------------------------------------
# Catálogo maestro (RF-01)
# ---------------------------------------------------------------------------

class Cliente(models.Model):
    razon_social = models.CharField(max_length=120)
    unidad_negocio = models.CharField(max_length=80, blank=True)

    class Meta:
        db_table = "cliente"
        verbose_name_plural = "Clientes"
        ordering = ["razon_social"]

    def __str__(self):
        return self.razon_social


class Local(models.Model):
    cliente = models.ForeignKey(Cliente, on_delete=models.PROTECT, related_name="locales")
    nombre = models.CharField(max_length=120)
    direccion = models.CharField(max_length=200)
    comuna = models.CharField(max_length=80)

    class Meta:
        db_table = "local"
        verbose_name_plural = "Locales"
        ordering = ["nombre"]

    def __str__(self):
        return self.nombre


class Tablero(models.Model):
    """Unidad de cobertura del proceso.

    Clave primaria subrogada (`id`) y no el código del tablero, porque el código
    es un dato de terreno que puede corregirse durante el levantamiento; si fuera
    la PK, corregirlo obligaría a reescribir todo el historial que lo referencia.
    La unicidad real del negocio se declara como índice único (local, código).
    """

    class Tipo(models.TextChoices):
        FUERZA = "FUERZA", "Tablero de fuerza"
        DISTRIBUCION = "DISTRIBUCION", "Tablero de distribución"
        ALUMBRADO = "ALUMBRADO", "Tablero de alumbrado"
        EMERGENCIA = "EMERGENCIA", "Tablero de emergencia"

    local = models.ForeignKey(Local, on_delete=models.PROTECT, related_name="tableros")
    codigo = models.CharField(max_length=40)
    ubicacion = models.CharField(max_length=150)
    tipo = models.CharField(max_length=20, choices=Tipo.choices, default=Tipo.DISTRIBUCION)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "tablero"
        verbose_name_plural = "Tableros"
        ordering = ["local", "codigo"]
        constraints = [
            models.UniqueConstraint(fields=["local", "codigo"], name="uq_tablero_local_codigo")
        ]

    def __str__(self):
        return f"{self.codigo} — {self.ubicacion}"


# ---------------------------------------------------------------------------
# Pauta de mantención (digitalización de la ficha N° 002190 de IMELSE)
# ---------------------------------------------------------------------------

class SeccionChecklist(models.Model):
    numero = models.PositiveSmallIntegerField(unique=True)
    nombre = models.CharField(max_length=150)

    class Meta:
        db_table = "seccion_checklist"
        verbose_name_plural = "Secciones del checklist"
        ordering = ["numero"]

    def __str__(self):
        return f"{self.numero}. {self.nombre}"


class ItemChecklist(models.Model):
    class Ambito(models.TextChoices):
        TABLERO = "TABLERO", "Por tablero"
        VISITA = "VISITA", "Por visita"

    seccion = models.ForeignKey(SeccionChecklist, on_delete=models.PROTECT, related_name="items")
    orden = models.PositiveSmallIntegerField()
    descripcion = models.CharField(max_length=250)
    ambito = models.CharField(max_length=10, choices=Ambito.choices, default=Ambito.TABLERO)
    obligatorio = models.BooleanField(default=True)

    class Meta:
        db_table = "item_checklist"
        verbose_name_plural = "Ítems del checklist"
        ordering = ["seccion__numero", "orden"]
        constraints = [
            models.UniqueConstraint(fields=["seccion", "orden"], name="uq_item_seccion_orden")
        ]

    @property
    def codigo(self):
        return f"{self.seccion.numero}.{self.orden}"

    def __str__(self):
        return f"{self.codigo} {self.descripcion}"


# ---------------------------------------------------------------------------
# Planificación (RF-02)
# ---------------------------------------------------------------------------

class Ciclo(models.Model):
    """Ciclo bimensual de mantención preventiva bajo contrato."""

    anio = models.PositiveSmallIntegerField()
    periodo = models.PositiveSmallIntegerField(help_text="1 a 6 (ciclos bimensuales)")
    fecha_inicio = models.DateField()

    class Meta:
        db_table = "ciclo"
        verbose_name_plural = "Ciclos"
        ordering = ["-anio", "-periodo"]
        constraints = [
            models.UniqueConstraint(fields=["anio", "periodo"], name="uq_ciclo_anio_periodo")
        ]

    def __str__(self):
        return f"Ciclo {self.periodo}/{self.anio}"

    # -- Calendario del contrato (RF-02) ------------------------------------

    DURACION_DIAS = 60  # el contrato con el cliente es bimensual

    @property
    def fecha_termino(self):
        return self.fecha_inicio + timedelta(days=self.DURACION_DIAS - 1)

    @property
    def vigente(self):
        return self.fecha_inicio <= timezone.localdate() <= self.fecha_termino

    def locales_del_contrato(self):
        """Locales con al menos un tablero activo en el catálogo.

        El alcance del ciclo no se declara a mano: sale del catálogo, que es la
        misma fuente que define el denominador de la cobertura. Si un local no
        tiene tableros activos, tampoco tiene nada que mantener.
        """
        return Local.objects.filter(tableros__activo=True).distinct()

    def locales_sin_visita(self):
        con_visita = set(self.visitas.values_list("local_id", flat=True))
        return [l for l in self.locales_del_contrato() if l.id not in con_visita]

    def generar_visitas(self):
        """RF-02: crea una visita planificada por cada local del contrato.

        Las fechas se reparten dentro de la ventana del ciclo en vez de caer
        todas el primer día: una cuadrilla no puede visitar cuatro locales la
        misma mañana, y una planificación que lo propone no sirve para
        despachar a nadie.

        Es idempotente. Un local que ya tiene visita en el ciclo no se duplica,
        por dos razones que conviene distinguir: la restricción única
        (local, ciclo) lo prohíbe en la base, y además volver a apretar el
        botón no debe cambiar nada de lo que ya existe. Lo primero protege la
        integridad; lo segundo protege al usuario.
        """
        faltantes = self.locales_sin_visita()
        if not faltantes:
            return []
        paso = max(1, (self.DURACION_DIAS - 10) // len(faltantes))
        creadas = []
        for i, local in enumerate(faltantes):
            creadas.append(
                Visita.objects.create(
                    local=local,
                    ciclo=self,
                    fecha=self.fecha_inicio + timedelta(days=3 + i * paso),
                )
            )
        return creadas


class Visita(models.Model):
    class Estado(models.TextChoices):
        PLANIFICADA = "PLANIFICADA", "Planificada"
        EN_EJECUCION = "EN_EJECUCION", "En ejecución"
        CERRADA = "CERRADA", "Cerrada"

    local = models.ForeignKey(Local, on_delete=models.PROTECT, related_name="visitas")
    ciclo = models.ForeignKey(Ciclo, on_delete=models.PROTECT, related_name="visitas")
    fecha = models.DateField()
    estado = models.CharField(max_length=15, choices=Estado.choices, default=Estado.PLANIFICADA)
    cuadrilla = models.ManyToManyField(
        settings.AUTH_USER_MODEL, related_name="visitas", blank=True,
        db_table="visita_cuadrilla",
    )
    cerrada_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="visitas_cerradas",
    )
    ts_cierre = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "visita"
        verbose_name_plural = "Visitas"
        ordering = ["-fecha"]
        constraints = [
            models.UniqueConstraint(fields=["local", "ciclo"], name="uq_visita_local_ciclo")
        ]

    def __str__(self):
        return f"{self.local.nombre} — {self.fecha:%d/%m/%Y}"

    # -- Cobertura (RF-06, RF-12) -------------------------------------------

    def tableros_esperados(self):
        return self.local.tableros.filter(activo=True)

    def tableros_registrados_ids(self):
        return set(
            self.registros_tablero.filter(cerrado=True).values_list("tablero_id", flat=True)
        )

    def tableros_pendientes_ids(self):
        return set(self.pendientes.values_list("tablero_id", flat=True))

    def tableros_sin_resolver(self):
        resueltos = self.tableros_registrados_ids() | self.tableros_pendientes_ids()
        return self.tableros_esperados().exclude(id__in=resueltos)

    @property
    def total_tableros(self):
        return self.tableros_esperados().count()

    @property
    def total_registrados(self):
        return len(self.tableros_registrados_ids())

    @property
    def porcentaje_cobertura(self):
        total = self.total_tableros
        return round(100 * self.total_registrados / total) if total else 0

    @property
    def puede_cerrarse(self):
        """RF-06: no se cierra mientras haya tableros sin registro ni pendiente declarado."""
        return self.estado != self.Estado.CERRADA and not self.tableros_sin_resolver().exists()

    def cerrar(self, usuario):
        if self.estado == self.Estado.CERRADA:
            raise ValidationError("La visita ya está cerrada.")
        if self.tableros_sin_resolver().exists():
            raise ValidationError(
                "No se puede cerrar la visita: quedan tableros sin registro ni "
                "pendiente declarado (RF-06)."
            )
        self.estado = self.Estado.CERRADA
        self.cerrada_por = usuario
        self.ts_cierre = timezone.now()
        self.save(update_fields=["estado", "cerrada_por", "ts_cierre"])


# ---------------------------------------------------------------------------
# Ejecución en terreno — registros inmutables
# ---------------------------------------------------------------------------

class RegistroTablero(models.Model):
    """Agrupa el trabajo declarado sobre un tablero dentro de una visita.

    Mientras `cerrado` es False el técnico aún está capturando; al cerrarlo, el
    conjunto queda sellado y sus ítems y evidencias ya no admiten cambios.
    """

    visita = models.ForeignKey(Visita, on_delete=models.PROTECT, related_name="registros_tablero")
    tablero = models.ForeignKey(Tablero, on_delete=models.PROTECT, related_name="registros")
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="registros_tablero"
    )
    ts_inicio = models.DateTimeField(default=timezone.now)
    ts_cierre = models.DateTimeField(null=True, blank=True)
    cerrado = models.BooleanField(default=False)

    class Meta:
        db_table = "registro_tablero"
        verbose_name_plural = "Registros por tablero"
        ordering = ["-ts_inicio"]

    def __str__(self):
        return f"{self.tablero.codigo} @ {self.visita}"

    def delete(self, *args, **kwargs):
        if self.cerrado:
            raise PermissionDenied("Un registro de tablero cerrado no puede eliminarse (RNF-02).")
        return super().delete(*args, **kwargs)

    def sellar(self):
        if self.cerrado:
            raise ValidationError("Este registro ya está cerrado.")
        if not self.evidencias.exists():
            raise ValidationError(
                "RF-04: se exige al menos una fotografía por tablero intervenido."
            )
        faltantes = self.items_faltantes()
        if faltantes:
            raise ValidationError(
                f"Faltan {len(faltantes)} ítems obligatorios de la pauta por responder."
            )
        sin_prueba = self.items_sin_evidencia()
        if sin_prueba:
            raise ValidationError(
                f"RF-03: {len(sin_prueba)} ítem(s) marcados como ejecutados no "
                "tienen fotografía vinculada. Un ítem no puede declararse hecho "
                "sin su evidencia."
            )
        self.cerrado = True
        self.ts_cierre = timezone.now()
        self.save(update_fields=["cerrado", "ts_cierre"])

    # -- Estado de la pauta --------------------------------------------------

    def respuestas_vigentes(self):
        """Última respuesta registrada para cada ítem (las anteriores siguen en la tabla)."""
        vigentes = {}
        for r in self.items.select_related("item").order_by("ts_captura", "id"):
            vigentes[r.item_id] = r
        return vigentes

    def items_faltantes(self):
        esperados = ItemChecklist.objects.filter(
            ambito=ItemChecklist.Ambito.TABLERO, obligatorio=True
        )
        respondidos = set(self.respuestas_vigentes())
        return [i for i in esperados if i.id not in respondidos]

    def items_sin_evidencia(self):
        """Ítems declarados ejecutados («Sí») que no tienen ninguna foto vinculada.

        Implementa RF-03 al pie de la letra: el sistema «no permite marcar un
        ítem como ejecutado sin registrar su evidencia asociada». Una misma
        fotografía puede respaldar varios ítems, de modo que la regla no obliga
        a repetir quince capturas casi idénticas del mismo tablero.
        """
        con_foto = set()
        for evidencia in self.evidencias.prefetch_related("items"):
            con_foto.update(evidencia.items.values_list("id", flat=True))
        return [
            r.item
            for r in self.respuestas_vigentes().values()
            if r.resultado == RegistroItem.Resultado.SI and r.item_id not in con_foto
        ]


class RegistroItem(AppendOnlyModel):
    """Respuesta a un ítem de la pauta. Inmutable (RNF-02).

    Una corrección no sobrescribe: crea una fila nueva con `corrige_a` apuntando
    a la original. El informe muestra la vigente; el historial muestra la cadena.
    """

    class Resultado(models.TextChoices):
        SI = "SI", "Sí"
        NO = "NO", "No"
        NA = "NA", "No aplica"

    registro_tablero = models.ForeignKey(
        RegistroTablero,
        on_delete=models.PROTECT,
        related_name="items",
        null=True,
        blank=True,
        help_text="Nulo para ítems de ámbito visita.",
    )
    visita = models.ForeignKey(Visita, on_delete=models.PROTECT, related_name="items")
    item = models.ForeignKey(ItemChecklist, on_delete=models.PROTECT, related_name="registros")
    resultado = models.CharField(max_length=2, choices=Resultado.choices)
    justificacion = models.TextField(
        blank=True,
        help_text="Obligatoria cuando el resultado es «No» o «No aplica».",
    )
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="items_registrados"
    )
    ts_captura = models.DateTimeField(default=timezone.now)
    corrige_a = models.ForeignKey(
        "self",
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="correcciones",
    )

    class Meta:
        db_table = "registro_item"
        verbose_name_plural = "Registros de ítem"
        ordering = ["item__seccion__numero", "item__orden", "ts_captura"]

    def __str__(self):
        return f"{self.item.codigo} = {self.resultado}"

    @property
    def vigente(self):
        """True si ninguna corrección posterior lo reemplaza."""
        return not self.correcciones.exists()


class Evidencia(AppendOnlyModel):
    """Fotografía de respaldo (RF-04, RF-05).

    El `hash_sha256` se calcula al subir el archivo y se almacena junto al
    registro: permite comprobar más tarde que la imagen exhibida es exactamente
    la que se capturó en terreno. Fecha, hora y autor los pone el sistema, nunca
    el operador (RF-05).
    """

    registro_tablero = models.ForeignKey(
        RegistroTablero, on_delete=models.PROTECT, related_name="evidencias"
    )
    items = models.ManyToManyField(
        ItemChecklist,
        related_name="evidencias",
        blank=True,
        db_table="evidencia_item",
        help_text=(
            "Ítems de la pauta que esta fotografía respalda (RF-03, RF-04). "
            "Una captura puede evidenciar varios ítems del mismo tablero: la "
            "foto de las protecciones generales respalda tanto su revisión de "
            "estado como su reapriete."
        ),
    )
    archivo = models.ImageField(upload_to="evidencias/%Y/%m/")
    hash_sha256 = models.CharField(max_length=64, editable=False)
    bytes = models.PositiveIntegerField(default=0, editable=False)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="evidencias"
    )
    ts = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "evidencia"
        verbose_name_plural = "Evidencias"
        ordering = ["ts"]

    def __str__(self):
        return f"Evidencia {self.pk} — {self.registro_tablero.tablero.codigo}"

    def save(self, *args, **kwargs):
        if self.pk is None and self.archivo and not self.hash_sha256:
            digest = hashlib.sha256()
            self.archivo.open("rb")
            for bloque in iter(lambda: self.archivo.read(65536), b""):
                digest.update(bloque)
            self.archivo.seek(0)
            self.hash_sha256 = digest.hexdigest()
            self.bytes = self.archivo.size
        return super().save(*args, **kwargs)

    @property
    def hash_corto(self):
        return self.hash_sha256[:12]


class Observacion(AppendOnlyModel):
    """Comentario adjunto a un registro, sin potestad para alterarlo.

    Es el canal por el que el estudiante dual (o cualquier integrante de la
    cuadrilla distinto del responsable) aporta lo que ve sin tocar lo declarado.
    """

    registro_tablero = models.ForeignKey(
        RegistroTablero, on_delete=models.PROTECT, related_name="observaciones"
    )
    registro_item = models.ForeignKey(
        RegistroItem,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="observaciones",
    )
    autor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="observaciones"
    )
    texto = models.TextField()
    ts = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "observacion"
        verbose_name_plural = "Observaciones"
        ordering = ["ts"]

    def __str__(self):
        return f"Observación de {self.autor} ({self.ts:%d/%m %H:%M})"


class Pendiente(models.Model):
    """Declaración explícita de un tablero no intervenido (RF-07).

    Es la única salida legítima para cerrar una visita con cobertura incompleta:
    obliga a nombrar el motivo en lugar de dejar el silencio del papel.
    """

    class Motivo(models.TextChoices):
        SIN_ACCESO = "SIN_ACCESO", "Sala sin acceso / llave no disponible"
        EN_OPERACION = "EN_OPERACION", "Equipo en operación, no se pudo desenergizar"
        SIN_MATERIAL = "SIN_MATERIAL", "Falta de material o repuesto"
        TIEMPO = "TIEMPO", "Tiempo insuficiente en ventana del local"
        NO_EXISTE = "NO_EXISTE", "Tablero no existe o fue retirado"
        OTRO = "OTRO", "Otro (detallar)"

    #: Motivos que no se resuelven solos en el ciclo siguiente y que por eso
    #: escalan a gerencia. «Tiempo insuficiente» no está en la lista: es ruido
    #: operativo normal y se corrige reprogramando la ruta. Esta definición es
    #: única a propósito: el panel, el flujo de n8n y las consultas tienen que
    #: considerar críticos exactamente los mismos motivos.
    MOTIVOS_CRITICOS = ("SIN_ACCESO", "EN_OPERACION", "NO_EXISTE")

    visita = models.ForeignKey(Visita, on_delete=models.PROTECT, related_name="pendientes")
    tablero = models.ForeignKey(Tablero, on_delete=models.PROTECT, related_name="pendientes")
    motivo = models.CharField(max_length=20, choices=Motivo.choices)
    comentario = models.TextField(blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="pendientes"
    )
    ts = models.DateTimeField(default=timezone.now)

    class Meta:
        db_table = "pendiente"
        verbose_name_plural = "Pendientes"
        ordering = ["-ts"]
        constraints = [
            models.UniqueConstraint(fields=["visita", "tablero"], name="uq_pendiente_visita_tablero")
        ]

    def __str__(self):
        return f"Pendiente {self.tablero.codigo} — {self.get_motivo_display()}"


class Hallazgo(AppendOnlyModel):
    """Anomalía detectada durante la visita, clasificada por criticidad (RF-10)."""

    class Criticidad(models.TextChoices):
        BAJA = "BAJA", "Baja"
        MEDIA = "MEDIA", "Media"
        ALTA = "ALTA", "Alta"
        CRITICA = "CRITICA", "Crítica"

    registro_tablero = models.ForeignKey(
        RegistroTablero, on_delete=models.PROTECT, related_name="hallazgos"
    )
    criticidad = models.CharField(max_length=10, choices=Criticidad.choices)
    descripcion = models.TextField()
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="hallazgos"
    )
    ts = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "hallazgo"
        verbose_name_plural = "Hallazgos"
        ordering = ["-ts"]

    def __str__(self):
        return f"[{self.get_criticidad_display()}] {self.descripcion[:50]}"


# ---------------------------------------------------------------------------
# Abastecimiento (RF-11) — materiales y repuestos faltantes
# ---------------------------------------------------------------------------

class MaterialFaltante(AppendOnlyModel):
    """Material o repuesto que faltó en terreno (RF-11).

    Ataca la manifestación P6 del diagnóstico, el re-trabajo en abastecimiento.
    Hoy el técnico avisa por mensajería o lo comenta al volver, y la compra se
    hace cuando alguien se acuerda. El resultado medido en el levantamiento es
    que la cuadrilla vuelve al mismo local sin el repuesto y el tablero queda
    pendiente por segunda vez, con el mismo motivo.

    Se asocia a la **visita**, que es lo que exige el requisito, y a través de
    ella al local. El **tablero es opcional** y eso es deliberado: hay
    faltantes que bloquean un tablero concreto y faltantes de consumo general
    del local. Forzar la asociación al tablero en el segundo caso obligaría a
    inventar un dato, y un dato inventado contamina la consulta que después
    pregunta qué comprar.

    Es append-only como todo registro de terreno. Marcar un faltante como
    comprado sería una entidad distinta, del lado de abastecimiento, y queda
    declarada fuera del alcance de esta entrega.
    """

    class Unidad(models.TextChoices):
        UNIDAD = "UNIDAD", "Unidad"
        METRO = "METRO", "Metro"
        CAJA = "CAJA", "Caja"
        JUEGO = "JUEGO", "Juego"
        KILO = "KILO", "Kilogramo"
        LITRO = "LITRO", "Litro"

    class Urgencia(models.TextChoices):
        BLOQUEA = "BLOQUEA", "Bloquea la mantención del tablero"
        PROXIMO = "PROXIMO", "Reponer antes del próximo ciclo"
        STOCK = "STOCK", "Reposición de stock de la camioneta"

    visita = models.ForeignKey(
        Visita, on_delete=models.PROTECT, related_name="materiales_faltantes"
    )
    tablero = models.ForeignKey(
        Tablero,
        on_delete=models.PROTECT,
        null=True,
        blank=True,
        related_name="materiales_faltantes",
    )
    descripcion = models.CharField(max_length=200)
    cantidad = models.PositiveSmallIntegerField(default=1)
    unidad = models.CharField(max_length=10, choices=Unidad.choices, default=Unidad.UNIDAD)
    urgencia = models.CharField(
        max_length=10, choices=Urgencia.choices, default=Urgencia.PROXIMO
    )
    comentario = models.TextField(blank=True)
    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="materiales_faltantes"
    )
    ts = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "material_faltante"
        verbose_name = "Material faltante"
        verbose_name_plural = "Materiales faltantes"
        ordering = ["-ts"]
        constraints = [
            models.CheckConstraint(
                condition=models.Q(cantidad__gte=1),
                name="ck_material_cantidad_positiva",
            ),
            models.CheckConstraint(
                condition=~models.Q(descripcion=""),
                name="ck_material_descripcion_no_vacia",
            ),
        ]

    @property
    def local(self):
        return self.visita.local

    @property
    def bloqueante(self):
        return self.urgencia == self.Urgencia.BLOQUEA

    def __str__(self):
        return f"{self.cantidad} {self.get_unidad_display()} · {self.descripcion}"


# ---------------------------------------------------------------------------
# Mediciones eléctricas (RF-17) — digitalización de la hoja N° 002214
# ---------------------------------------------------------------------------

class MedicionElectrica(AppendOnlyModel):
    """Lecturas de la hoja «MEDICIONES ELECTRICAS» de IMELSE, por tablero.

    En papel esta hoja viene con tres columnas fijas (T.F.G., T.G. Emergencia y
    T.F.G. Alumbrado). Aquí se asocia al registro del tablero, de modo que la
    medición queda trazable al tablero concreto y no a una columna preimpresa:
    si el local tiene cinco tableros en vez de tres, el sistema no se queda sin
    casilleros.

    Valores nominales en Chile: 400 V entre fases, 230 V fase-neutro.
    """

    NOMINAL_FASE = 400
    NOMINAL_NEUTRO = 230
    TOLERANCIA = 0.08  # ±8 %, criterio operativo para marcar una lectura anómala

    registro_tablero = models.OneToOneField(
        RegistroTablero, on_delete=models.PROTECT, related_name="medicion"
    )

    # Tensión entre fases (V)
    v_l1_l2 = models.DecimalField("L1-L2 (V)", max_digits=7, decimal_places=2, null=True, blank=True)
    v_l2_l3 = models.DecimalField("L2-L3 (V)", max_digits=7, decimal_places=2, null=True, blank=True)
    v_l3_l1 = models.DecimalField("L3-L1 (V)", max_digits=7, decimal_places=2, null=True, blank=True)

    # Tensión línea-neutro (V)
    v_l1_n = models.DecimalField("L1-N (V)", max_digits=7, decimal_places=2, null=True, blank=True)
    v_l2_n = models.DecimalField("L2-N (V)", max_digits=7, decimal_places=2, null=True, blank=True)
    v_l3_n = models.DecimalField("L3-N (V)", max_digits=7, decimal_places=2, null=True, blank=True)

    # Tensión línea-tierra (V)
    v_l1_t = models.DecimalField("L1-T (V)", max_digits=7, decimal_places=2, null=True, blank=True)
    v_l2_t = models.DecimalField("L2-T (V)", max_digits=7, decimal_places=2, null=True, blank=True)
    v_l3_t = models.DecimalField("L3-T (V)", max_digits=7, decimal_places=2, null=True, blank=True)

    # Tensión tierra-neutro (V) — una lectura alta delata una tierra deficiente
    v_t_n = models.DecimalField("T-N (V)", max_digits=7, decimal_places=2, null=True, blank=True)

    # Corriente por fase (A)
    i_l1 = models.DecimalField("L1 (A)", max_digits=8, decimal_places=2, null=True, blank=True)
    i_l2 = models.DecimalField("L2 (A)", max_digits=8, decimal_places=2, null=True, blank=True)
    i_l3 = models.DecimalField("L3 (A)", max_digits=8, decimal_places=2, null=True, blank=True)

    cos_fi = models.DecimalField(
        "Lectura COS-FI", max_digits=4, decimal_places=3, null=True, blank=True,
        help_text="Factor de potencia, entre 0 y 1.",
    )
    observaciones = models.TextField(blank=True)

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="mediciones"
    )
    ts = models.DateTimeField(default=timezone.now, editable=False)

    class Meta:
        db_table = "medicion_electrica"
        verbose_name = "Medición eléctrica"
        verbose_name_plural = "Mediciones eléctricas"

    def __str__(self):
        return f"Mediciones {self.registro_tablero.tablero.codigo}"

    # -- Lectura del dato, no sólo almacenamiento ---------------------------

    def _fuera(self, valor, nominal):
        if valor is None:
            return False
        return abs(float(valor) - nominal) / nominal > self.TOLERANCIA

    def anomalias(self):
        """Lecturas fuera de rango. Alimenta la detección temprana (P5).

        Guardar el número no basta: si el sistema no sabe leerlo, reproduce el
        papel con otra tipografía.
        """
        avisos = []
        for campo, nominal in (
            ("v_l1_l2", self.NOMINAL_FASE), ("v_l2_l3", self.NOMINAL_FASE),
            ("v_l3_l1", self.NOMINAL_FASE),
            ("v_l1_n", self.NOMINAL_NEUTRO), ("v_l2_n", self.NOMINAL_NEUTRO),
            ("v_l3_n", self.NOMINAL_NEUTRO),
        ):
            valor = getattr(self, campo)
            if self._fuera(valor, nominal):
                avisos.append(
                    f"{self._meta.get_field(campo).verbose_name}: {valor} V "
                    f"(nominal {nominal} V)"
                )
        if self.v_t_n is not None and float(self.v_t_n) > 2:
            avisos.append(f"Tierra-neutro: {self.v_t_n} V (se espera cercana a 0 V)")
        if self.cos_fi is not None and float(self.cos_fi) < 0.93:
            avisos.append(f"COS-FI: {self.cos_fi} (bajo el 0,93 exigido por norma)")

        corrientes = [float(x) for x in (self.i_l1, self.i_l2, self.i_l3) if x is not None]
        if len(corrientes) == 3 and max(corrientes) > 0:
            media = sum(corrientes) / 3
            if media > 0 and (max(corrientes) - min(corrientes)) / media > 0.15:
                avisos.append(
                    f"Desequilibrio de corriente entre fases: "
                    f"{min(corrientes):.1f} a {max(corrientes):.1f} A"
                )
        return avisos

    @property
    def tiene_anomalias(self):
        return bool(self.anomalias())


# ---------------------------------------------------------------------------
# Informe despachable (RF-13)
# ---------------------------------------------------------------------------

class InformeVisita(AppendOnlyModel):
    """Informe de mantención generado y archivado en la base de datos.

    Se genera al cerrar la visita y queda guardado con su propio hash: el
    documento que se envía al cliente es un objeto del sistema, no un archivo
    que alguien arma a mano y puede alterar antes de mandarlo. Regenerar crea
    una versión nueva; las anteriores no se borran.
    """

    visita = models.ForeignKey(Visita, on_delete=models.PROTECT, related_name="informes")
    version = models.PositiveSmallIntegerField(default=1)
    archivo = models.FileField(upload_to="informes/%Y/%m/")
    hash_sha256 = models.CharField(max_length=64, editable=False)
    bytes = models.PositiveIntegerField(default=0, editable=False)
    generado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name="informes"
    )
    ts = models.DateTimeField(default=timezone.now, editable=False)

    # Despacho al cliente
    destinatario = models.EmailField(blank=True)
    ts_despacho = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = "informe_visita"
        verbose_name = "Informe de visita"
        verbose_name_plural = "Informes de visita"
        ordering = ["-ts"]
        constraints = [
            models.UniqueConstraint(fields=["visita", "version"], name="uq_informe_visita_version")
        ]

    def __str__(self):
        return f"Informe v{self.version} — {self.visita}"

    def save(self, *args, **kwargs):
        if self.pk is None and self.archivo and not self.hash_sha256:
            digest = hashlib.sha256()
            self.archivo.open("rb")
            for bloque in iter(lambda: self.archivo.read(65536), b""):
                digest.update(bloque)
            self.archivo.seek(0)
            self.hash_sha256 = digest.hexdigest()
            self.bytes = self.archivo.size
        return super().save(*args, **kwargs)

    @property
    def hash_corto(self):
        return self.hash_sha256[:12]

    def marcar_despachado(self, destinatario):
        """El despacho es el único dato que se puede añadir después de generado.

        No altera el documento ni su hash: registra a quién y cuándo se envió.
        """
        InformeVisita.objects.filter(pk=self.pk).update(
            destinatario=destinatario, ts_despacho=timezone.now()
        )


# ---------------------------------------------------------------------------
# Libro anual de control (Excel con una hoja por mes)
# ---------------------------------------------------------------------------

class LibroAnual(models.Model):
    """Planilla anual de control, con una hoja por mes.

    A diferencia de `InformeVisita`, este modelo **no** es append-only, y la
    diferencia es deliberada: el libro no es evidencia, es una vista derivada
    de lo que ya está en la base de datos. Se regenera completo cada vez que
    los datos cambian, de modo que el archivo y el sistema nunca puedan decir
    cosas distintas.

    La evidencia inmutable son los registros de terreno y el PDF de cada
    visita. Esta planilla es la herramienta de trabajo de la gerencia.
    """

    anio = models.PositiveSmallIntegerField(unique=True)
    archivo = models.FileField(upload_to="libros/", blank=True)
    n_visitas = models.PositiveSmallIntegerField(default=0)
    bytes = models.PositiveIntegerField(default=0)
    ts_actualizacion = models.DateTimeField(null=True, blank=True)
    actualizado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="libros",
    )

    class Meta:
        db_table = "libro_anual"
        verbose_name = "Libro anual"
        verbose_name_plural = "Libros anuales"
        ordering = ["-anio"]

    def __str__(self):
        return f"Control de mantención {self.anio}"
