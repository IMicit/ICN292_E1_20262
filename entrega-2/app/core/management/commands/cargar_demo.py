"""Carga un escenario de demostración con datos enteramente ficticios.

Compromiso declarado en el informe de la Entrega 1 (sección de Ley 21.719):
el prototipo opera exclusivamente con datos ficticios. En consecuencia, aquí
no hay nombres reales de trabajadores de IMELSE, ni códigos o direcciones
reales de locales del cliente, ni fotografías tomadas en instalaciones reales.
Las imágenes de evidencia se generan sintéticamente al vuelo.
"""

import io
import random
from datetime import date, timedelta

from django.core.files.base import ContentFile
from django.core.management import call_command
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from PIL import Image, ImageDraw

from core.models import (
    Ciclo,
    InformeVisita,
    MedicionElectrica,
    Cliente,
    Evidencia,
    Hallazgo,
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

USUARIOS = [
    ("tecnico",  "Rodrigo",  "Pérez",    Usuario.Rol.TECNICO),
    ("tecnico2", "Camila",   "Soto",     Usuario.Rol.TECNICO),
    ("dual",     "Ignacio",  "Vera",     Usuario.Rol.TECNICO),
    ("admin",    "Valeria",  "Muñoz",    Usuario.Rol.ADMINISTRACION),
    ("gerencia", "Andrés",   "Carrasco", Usuario.Rol.GERENCIA),
]
CLAVE = "imelse2026"

LOCALES = [
    ("Sucursal Norte",    "Av. Ficticia 1200",   "Comuna Demo A", 6),
    ("Sucursal Oriente",  "Calle Ejemplo 455",   "Comuna Demo B", 5),
    ("Sucursal Poniente", "Pasaje Simulado 78",  "Comuna Demo C", 4),
    ("Sucursal Centro",   "Av. Prototipo 3390",  "Comuna Demo D", 7),
]

UBICACIONES = [
    "Sala eléctrica principal", "Bodega de recepción", "Subterráneo -1",
    "Pasillo de cámaras", "Sala de máquinas", "Andén de carga", "Entrepiso",
]
TIPOS = [t[0] for t in Tablero.Tipo.choices]

MOTIVOS = [
    "No corresponde a este tipo de tablero.",
    "Componente no presente en el equipo.",
    "Sin acceso al elemento durante la ventana del local.",
    "Requiere desenergizar; se reprograma.",
]

PALETA = ["#2f4f6f", "#4a5d52", "#6b5540", "#3d4a5c", "#55483f"]

# Materiales de la demostración (RF-11). Son consumibles y repuestos eléctricos
# corrientes, no catálogo real de ningún proveedor.
CATALOGO_FALTANTES = [
    ("Automático diferencial 2x25A, curva C", 1, "UNIDAD", "BLOQUEA",
     "Diferencial del circuito de alumbrado quemado; sin repuesto en la camioneta."),
    ("Prensaestopa PG-16", 4, "UNIDAD", "PROXIMO",
     "Faltan en las entradas de la canalización inferior."),
    ("Cinta aislante de goma autofundente", 2, "UNIDAD", "STOCK", ""),
    ("Terminal de compresión 16 mm²", 10, "UNIDAD", "PROXIMO",
     "Los existentes están sulfatados; reemplazar el próximo ciclo."),
    ("Barra de tierra de cobre 1 m", 1, "UNIDAD", "BLOQUEA",
     "Puesta a tierra del tablero cortada; no se deja operativo sin reponerla."),
    ("Canaleta ranurada 40x40", 3, "METRO", "PROXIMO", ""),
]

# Qué faltante ocurre en qué visita, indexado por (periodo del ciclo, orden del
# local). Está escrito a mano y no sorteado, porque la demostración necesita
# mostrar dos patrones que significan cosas distintas:
#
#   · el faltante que deja un tablero sin poder mantenerse, que es una compra
#     urgente y cuesta cobertura en el ciclo siguiente;
#   · el consumible que falta una y otra vez en el mismo local, que no es un
#     olvido sino un error de stock permanente de la camioneta.
#
# El segundo patrón es el que el checklist en papel nunca pudo mostrar, porque
# cada hoja se miraba sola. Si los faltantes se sortearan, ninguno se repetiría
# y la consulta 6 tendría una rama que nunca se cumple.
FALTANTES_DEMO = {
    # Prensaestopa que falta tres veces en el mismo local: error de stock.
    (1, 1): [1],
    (3, 1): [1],
    (5, 1): [1],
    # Cinta aislante que falta dos veces en otro local.
    (2, 3): [2],
    (4, 3): [2],
    # Faltantes que detienen un tablero, repartidos en el año.
    (2, 0): [0],
    (4, 2): [0],
    (5, 3): [4],
    (6, 1): [0],
    # Reposiciones corrientes, sin tablero detenido.
    (1, 2): [3],
    (1, 3): [3],
    (3, 2): [2],
    (4, 0): [5],
    (4, 1): [5],
    (6, 0): [3],
}


def imagen_sintetica(etiqueta):
    """Genera una fotografía de evidencia simulada, sin origen real."""
    img = Image.new("RGB", (1200, 900), random.choice(PALETA))
    dib = ImageDraw.Draw(img)
    for _ in range(14):
        x, y = random.randint(0, 1100), random.randint(0, 800)
        dib.rectangle([x, y, x + random.randint(40, 180), y + random.randint(30, 120)],
                      outline="#cdd6e0", width=3)
    dib.rectangle([40, 40, 1160, 150], fill="#101820")
    dib.text((70, 70), f"EVIDENCIA SIMULADA — {etiqueta}", fill="#ffc107")
    dib.text((70, 105), "Prototipo academico ICN-292 · dato ficticio", fill="#8fa3b8")
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=78, optimize=True)
    return ContentFile(buf.getvalue(), name=f"demo-{etiqueta}.jpg")


class Command(BaseCommand):
    help = "Carga usuarios, catálogo, ciclos y visitas de demostración (datos ficticios)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--reiniciar",
            action="store_true",
            help="Borra los datos de demostración antes de volver a cargarlos.",
        )

    @transaction.atomic
    def handle(self, *args, **opciones):
        random.seed(292)

        if opciones["reiniciar"]:
            for modelo in (Observacion, Hallazgo, InformeVisita, MedicionElectrica,
                           Evidencia, RegistroItem, RegistroTablero, Pendiente,
                           Visita, Tablero, Local, Cliente, Ciclo):
                # Los modelos append-only bloquean delete() por instancia; el
                # borrado masivo del queryset se reserva a este comando de demo.
                modelo.objects.all().delete()
            Usuario.objects.filter(is_superuser=False).delete()

        call_command("cargar_pauta")

        # --- Usuarios ------------------------------------------------------
        usuarios = {}
        for username, nombre, apellido, rol in USUARIOS:
            u, creado = Usuario.objects.get_or_create(
                username=username,
                defaults={"first_name": nombre, "last_name": apellido, "rol": rol},
            )
            if creado:
                u.set_password(CLAVE)
                u.save()
            usuarios[username] = u

        if not Usuario.objects.filter(username="super").exists():
            Usuario.objects.create_superuser(
                "super", "super@ejemplo.cl", CLAVE,
                first_name="Super", last_name="Usuario",
                rol=Usuario.Rol.GERENCIA,
            )

        # --- Catálogo ------------------------------------------------------
        cliente, _ = Cliente.objects.get_or_create(
            razon_social="Cliente Retail Demo S.A.",
            defaults={"unidad_negocio": "Supermercados (ficticio)"},
        )

        locales = []
        for nombre, direccion, comuna, n_tableros in LOCALES:
            local, _ = Local.objects.get_or_create(
                cliente=cliente, nombre=nombre,
                defaults={"direccion": direccion, "comuna": comuna},
            )
            for i in range(1, n_tableros + 1):
                Tablero.objects.get_or_create(
                    local=local, codigo=f"TD-{local.pk:02d}{i:02d}",
                    defaults={
                        "ubicacion": UBICACIONES[(i - 1) % len(UBICACIONES)],
                        "tipo": TIPOS[(i - 1) % len(TIPOS)],
                    },
                )
            locales.append(local)

        # --- Ciclos: el año completo ---------------------------------------
        # Seis ciclos bimensuales. Con sólo dos, las consultas de negocio no
        # tienen de dónde sacar tendencias ni pueden mostrar un tablero que
        # lleva varios ciclos sin intervención, que es justamente el problema
        # que el sistema existe para detectar.
        hoy = date.today()
        anio = hoy.year
        ciclos = []
        for periodo in range(1, 7):
            inicio = date(anio, 2 * periodo - 1, 1)
            ciclo, _ = Ciclo.objects.get_or_create(
                anio=anio, periodo=periodo, defaults={"fecha_inicio": inicio}
            )
            ciclos.append(ciclo)

        items_tablero = list(ItemChecklist.objects.filter(ambito=ItemChecklist.Ambito.TABLERO))
        items_visita = list(ItemChecklist.objects.filter(ambito=ItemChecklist.Ambito.VISITA))

        # Dos tableros quedan pendientes ciclo tras ciclo. No es relleno: es el
        # caso que motiva el proyecto, y sin él las consultas de seguimiento
        # devuelven cero filas y no demuestran nada.
        cronicos = {
            locales[1].tableros.order_by("codigo").last().id:
                (Pendiente.Motivo.SIN_ACCESO,
                 "Sala cerrada con llave; el encargado no estaba en el local."),
            locales[3].tableros.order_by("codigo").last().id:
                (Pendiente.Motivo.EN_OPERACION,
                 "Equipo en operación continua; no se autorizó desenergizar."),
        }

        tecnicos = [usuarios["tecnico"], usuarios["tecnico2"]]

        for c, ciclo in enumerate(ciclos):
            en_curso = ciclo is ciclos[-1]          # el último ciclo sigue abierto
            for i, local in enumerate(locales):
                fecha = ciclo.fecha_inicio + timedelta(days=5 + i * 4)
                if fecha > hoy:
                    fecha = hoy - timedelta(days=max(0, 3 - i))
                tecnico = tecnicos[(c + i) % 2]
                visita = self._visita(local, ciclo, fecha, usuarios, tecnico)
                tableros = list(local.tableros.order_by("codigo"))

                if en_curso:
                    # Grados de avance distintos, para que el panel muestre
                    # una visita completa, una a medias y una sin empezar.
                    avance = [1.0, 0.5, 0.0, 0.25][i % 4]
                    objetivo = tableros[:int(len(tableros) * avance)]
                else:
                    objetivo = [t for t in tableros if t.id not in cronicos]
                    # Algún pendiente suelto, además de los crónicos.
                    if (c + i) % 5 == 0 and len(objetivo) > 2:
                        objetivo = objetivo[:-1]

                for t in objetivo:
                    self._registro(visita, t, tecnico, items_tablero)

                if not en_curso:
                    for t in tableros:
                        if t in objetivo:
                            continue
                        motivo, comentario = cronicos.get(
                            t.id, (Pendiente.Motivo.TIEMPO,
                                   "Ventana de atención del local insuficiente.")
                        )
                        Pendiente.objects.get_or_create(
                            visita=visita, tablero=t,
                            defaults={"motivo": motivo, "comentario": comentario,
                                      "usuario": tecnico},
                        )

                self._faltantes(visita, tecnico, tableros, i)

                if objetivo:
                    self._items_visita(visita, tecnico, items_visita)
                    visita.estado = Visita.Estado.EN_EJECUCION
                    visita.save(update_fields=["estado"])

                if visita.puede_cerrarse and (not en_curso or avance == 1.0):
                    visita.cerrar(tecnico)
                visita.refresh_from_db()
                self._fechar(visita)

        self.stdout.write(self.style.SUCCESS(
            f"Demo cargada: {Local.objects.count()} locales, "
            f"{Tablero.objects.count()} tableros, {Visita.objects.count()} visitas, "
            f"{Evidencia.objects.count()} evidencias."
        ))
        self.stdout.write("")
        self.stdout.write("Usuarios de prueba (clave «%s» para todos):" % CLAVE)
        for username, nombre, apellido, rol in USUARIOS:
            self.stdout.write(f"  {username:<10} {nombre} {apellido:<10} {rol}")
        self.stdout.write(f"  {'super':<10} acceso al panel de administración de Django")

    # -- auxiliares ---------------------------------------------------------

    def _visita(self, local, ciclo, fecha, usuarios, tecnico=None):
        visita, _ = Visita.objects.get_or_create(
            local=local, ciclo=ciclo, defaults={"fecha": fecha}
        )
        visita.cuadrilla.set([tecnico or usuarios["tecnico"], usuarios["dual"]])
        return visita

    def _fechar(self, visita):
        """Lleva las marcas de tiempo al día en que ocurrió la visita.

        Sin esto, todos los registros del año quedarían con la hora en que se
        cargó la demostración, y cualquier consulta que mire el tiempo —la
        latencia del registro, por ejemplo— devolvería un número sin sentido.
        Un dato de prueba que no resiste una consulta temporal no sirve para
        demostrar nada.
        """
        from datetime import datetime, time as _time

        tz = timezone.get_current_timezone()
        inicio = timezone.make_aware(datetime.combine(visita.fecha, _time(8, 30)), tz)

        registros = list(visita.registros_tablero.order_by("id"))
        for n, r in enumerate(registros):
            abre = inicio + timedelta(minutes=25 * n)
            cierra = abre + timedelta(minutes=random.randint(12, 22))
            RegistroTablero.objects.filter(pk=r.pk).update(
                ts_inicio=abre, ts_cierre=cierra if r.cerrado else None
            )
            RegistroItem.objects.filter(registro_tablero=r).update(ts_captura=abre)
            Evidencia.objects.filter(registro_tablero=r).update(ts=abre + timedelta(minutes=6))
            Hallazgo.objects.filter(registro_tablero=r).update(ts=cierra)
            MedicionElectrica.objects.filter(registro_tablero=r).update(ts=cierra)
            ultimo = cierra

        ultimo = locals().get("ultimo", inicio)
        RegistroItem.objects.filter(visita=visita, registro_tablero__isnull=True).update(
            ts_captura=ultimo
        )
        Pendiente.objects.filter(visita=visita).update(ts=ultimo + timedelta(minutes=4))
        MaterialFaltante.objects.filter(visita=visita).update(ts=ultimo + timedelta(minutes=6))
        Observacion.objects.filter(registro_tablero__visita=visita).update(
            ts=ultimo + timedelta(minutes=8)
        )
        if visita.estado == Visita.Estado.CERRADA:
            # RF-08: la evidencia queda disponible al cerrar, en terreno. El
            # cierre ocurre minutos después del último tablero, no al día
            # siguiente como pasaba con el papel.
            Visita.objects.filter(pk=visita.pk).update(
                ts_cierre=ultimo + timedelta(minutes=random.randint(3, 11))
            )

    def _faltantes(self, visita, tecnico, tableros, orden_local):
        """RF-11: materiales que faltaron durante la visita.

        No todas las visitas llevan faltantes, y eso es deliberado: si todas los
        tuvieran, la pantalla de abastecimiento se vería como una lista infinita
        en lugar de una lista de compras.
        """
        if visita.materiales_faltantes.exists():
            return
        indices = FALTANTES_DEMO.get((visita.ciclo.periodo, orden_local), [])
        for n, indice in enumerate(indices):
            descripcion, cantidad, unidad, urgencia, comentario = CATALOGO_FALTANTES[indice]
            tablero = None
            if urgencia == "BLOQUEA" and tableros:
                tablero = tableros[(visita.ciclo.periodo + n) % len(tableros)]
            MaterialFaltante.objects.create(
                visita=visita,
                tablero=tablero,
                usuario=tecnico,
                descripcion=descripcion,
                cantidad=cantidad,
                unidad=unidad,
                urgencia=urgencia,
                comentario=comentario,
            )

    def _items_visita(self, visita, usuario, items):
        for item in items:
            if RegistroItem.objects.filter(
                visita=visita, registro_tablero=None, item=item
            ).exists():
                continue
            resultado = random.choices(["SI", "NO", "NA"], weights=[85, 7, 8])[0]
            RegistroItem.objects.create(
                visita=visita, registro_tablero=None, item=item,
                resultado=resultado,
                justificacion="" if resultado == "SI" else random.choice(MOTIVOS),
                usuario=usuario, ts_captura=timezone.now(),
            )

    def _registro(self, visita, tablero, usuario, items):
        if RegistroTablero.objects.filter(visita=visita, tablero=tablero).exists():
            return
        registro = RegistroTablero.objects.create(
            visita=visita, tablero=tablero, usuario=usuario
        )
        hubo_no = False
        ejecutados = []
        for item in items:
            resultado = random.choices(["SI", "NO", "NA"], weights=[88, 6, 6])[0]
            hubo_no = hubo_no or resultado == "NO"
            if resultado == "SI":
                ejecutados.append(item)
            RegistroItem.objects.create(
                visita=visita, registro_tablero=registro, item=item,
                resultado=resultado,
                justificacion="" if resultado == "SI" else random.choice(MOTIVOS),
                usuario=usuario, ts_captura=timezone.now(),
            )

        # RF-03: cada ítem ejecutado necesita respaldo fotográfico. Una captura
        # cubre varios ítems, igual que en terreno: la foto del tablero abierto
        # evidencia la revisión y el reapriete de lo que aparece en ella.
        for grupo in [ejecutados[i:i + 4] for i in range(0, len(ejecutados), 4)]:
            evidencia = Evidencia.objects.create(
                registro_tablero=registro,
                archivo=imagen_sintetica(tablero.codigo),
                usuario=usuario, ts=timezone.now(),
            )
            evidencia.items.set(grupo)

        # Mediciones eléctricas (RF-17), con alguna lectura fuera de rango.
        anomalo = random.random() < 0.25
        MedicionElectrica.objects.create(
            registro_tablero=registro,
            v_l1_l2=round(random.uniform(395, 405), 1),
            v_l2_l3=round(random.uniform(395, 405), 1),
            v_l3_l1=round(random.uniform(340, 360) if anomalo else random.uniform(395, 405), 1),
            v_l1_n=round(random.uniform(226, 234), 1),
            v_l2_n=round(random.uniform(226, 234), 1),
            v_l3_n=round(random.uniform(226, 234), 1),
            v_l1_t=round(random.uniform(226, 234), 1),
            v_l2_t=round(random.uniform(226, 234), 1),
            v_l3_t=round(random.uniform(226, 234), 1),
            v_t_n=round(random.uniform(3.0, 6.0) if anomalo else random.uniform(0.1, 1.2), 2),
            # Una instalación sana tiene las tres fases parejas; el desequilibrio
            # es justamente lo que delata un problema de reparto de carga.
            i_l1=round(base := random.uniform(42, 68), 1),
            i_l2=round(base * random.uniform(0.97, 1.03), 1),
            i_l3=round(base * (random.uniform(0.70, 0.82) if anomalo
                               else random.uniform(0.97, 1.03)), 1),
            cos_fi=round(random.uniform(0.86, 0.92) if anomalo else random.uniform(0.94, 0.99), 3),
            usuario=usuario, ts=timezone.now(),
        )

        if hubo_no:
            Hallazgo.objects.create(
                registro_tablero=registro,
                criticidad=random.choice(["BAJA", "MEDIA", "ALTA"]),
                descripcion="Se detecta componente fuera de norma durante la revisión.",
                usuario=usuario, ts=timezone.now(),
            )
        registro.sellar()
