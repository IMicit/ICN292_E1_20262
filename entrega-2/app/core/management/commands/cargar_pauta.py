"""Carga la pauta de mantención preventiva de IMELSE.

Transcripción literal de la ficha «LISTA DE CHEQUEO MANTENIMIENTO PREVENTIVO
ELECTRICO N° 002190» de Montajes e Instalaciones Eléctricas IMELSE SpA,
levantada en terreno (ver `assets/ev-05-ficha-checklist.pdf` del repositorio).

El sistema no inventa la pauta: la digitaliza. El `ambito` es la única adición
del rediseño, y distingue los ítems que se responden una vez por visita de los
que deben responderse tablero por tablero, que es justamente la trazabilidad
que el formato en papel no permitía.
"""

from django.core.management.base import BaseCommand
from django.db import transaction

from core.models import ItemChecklist, SeccionChecklist

TABLERO = ItemChecklist.Ambito.TABLERO
VISITA = ItemChecklist.Ambito.VISITA

PAUTA = [
    (1, "Materiales usados", [
        (1, "¿Los materiales usados son correctos?", VISITA),
        (2, "¿Se define marca y calidad de materiales según contratados?", VISITA),
        (3, "¿Se utilizan materiales de bodega o aportados por cliente?", VISITA),
    ]),
    (2, "Actividades de limpieza realizadas", [
        (1, "Se realiza limpieza de luminarias", VISITA),
        (2, "Se realiza limpieza de sala eléctrica", VISITA),
        (3, "Se realiza limpieza de tableros de fuerza y distribución", TABLERO),
        (4, "Se realiza inspección de chapas en tableros eléctricos", TABLERO),
    ]),
    (3, "Estado y situación de componentes eléctricos en tableros e instalaciones", [
        (1, "Se revisa estado de luces piloto", TABLERO),
        (2, "Se revisa estado de protecciones generales", TABLERO),
        (3, "Se revisa estado de interruptores tripolares", TABLERO),
        (4, "Se revisa estado de interruptores unipolares", TABLERO),
        (5, "Se revisa estado de barras de distribución", TABLERO),
        (6, "Se revisa estado de borneras", TABLERO),
    ]),
    (4, "Estado y situación de apriete de componentes eléctricos en tableros e instalaciones", [
        (1, "Se realiza reapriete de luces piloto", TABLERO),
        (2, "Se realiza reapriete de protecciones generales", TABLERO),
        (3, "Se realiza reapriete de interruptores tripolares", TABLERO),
        (4, "Se realiza reapriete de interruptores unipolares", TABLERO),
        (5, "Se realiza reapriete de barras de distribución", TABLERO),
        (6, "Se realiza reapriete de borneras", TABLERO),
        (7, "Se realiza medición termográfica en tableros", TABLERO),
    ]),
    (5, "Revisión e inspección de grupo electrógeno", [
        (1, "Se realiza medición de baterías", VISITA),
        (2, "Se revisa nivel de petróleo", VISITA),
        (3, "Se revisa selector en modo automático", VISITA),
        (4, "Se revisa interruptor general del grupo operativo", VISITA),
        (5, "Se revisa TTA del grupo operativo", VISITA),
    ]),
]


class Command(BaseCommand):
    help = "Carga las secciones e ítems de la pauta de mantención de IMELSE."

    @transaction.atomic
    def handle(self, *args, **opciones):
        n_items = 0
        for numero, nombre, items in PAUTA:
            seccion, _ = SeccionChecklist.objects.update_or_create(
                numero=numero, defaults={"nombre": nombre}
            )
            for orden, descripcion, ambito in items:
                ItemChecklist.objects.update_or_create(
                    seccion=seccion,
                    orden=orden,
                    defaults={
                        "descripcion": descripcion,
                        "ambito": ambito,
                        "obligatorio": True,
                    },
                )
                n_items += 1

        por_tablero = ItemChecklist.objects.filter(ambito=TABLERO).count()
        por_visita = ItemChecklist.objects.filter(ambito=VISITA).count()
        self.stdout.write(
            self.style.SUCCESS(
                f"Pauta cargada: {len(PAUTA)} secciones, {n_items} ítems "
                f"({por_tablero} por tablero, {por_visita} por visita)."
            )
        )
