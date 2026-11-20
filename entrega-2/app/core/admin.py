"""Panel de administración.

El catálogo maestro (clientes, locales, tableros, pauta, ciclos) es editable:
son datos de referencia que la empresa mantiene.

Los registros de ejecución NO lo son, ni siquiera aquí. Si la inmutabilidad
(RNF-02) sólo se defendiera en las vistas, el admin de Django sería la puerta
trasera por la que se reproduce el problema del papel.
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    Ciclo,
    InformeVisita,
    LibroAnual,
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
    SeccionChecklist,
    Tablero,
    Usuario,
    Visita,
)


class SoloLectura(admin.ModelAdmin):
    """Vista de consulta: ni alta, ni edición, ni baja desde el admin."""

    def has_add_permission(self, request, obj=None):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(Usuario)
class UsuarioAdmin(UserAdmin):
    list_display = ("username", "first_name", "last_name", "rol", "is_active")
    list_filter = ("rol", "is_active")
    fieldsets = UserAdmin.fieldsets + (("Perfil SIG", {"fields": ("rol",)}),)
    add_fieldsets = UserAdmin.add_fieldsets + (("Perfil SIG", {"fields": ("rol",)}),)


@admin.register(Cliente)
class ClienteAdmin(admin.ModelAdmin):
    list_display = ("razon_social", "unidad_negocio")


class TableroInline(admin.TabularInline):
    model = Tablero
    extra = 1


@admin.register(Local)
class LocalAdmin(admin.ModelAdmin):
    list_display = ("nombre", "cliente", "comuna")
    list_filter = ("cliente", "comuna")
    search_fields = ("nombre", "direccion")
    inlines = [TableroInline]


@admin.register(Tablero)
class TableroAdmin(admin.ModelAdmin):
    list_display = ("codigo", "local", "ubicacion", "tipo", "activo")
    list_filter = ("tipo", "activo", "local")
    search_fields = ("codigo", "ubicacion")


class ItemInline(admin.TabularInline):
    model = ItemChecklist
    extra = 1


@admin.register(SeccionChecklist)
class SeccionAdmin(admin.ModelAdmin):
    list_display = ("numero", "nombre")
    inlines = [ItemInline]


@admin.register(ItemChecklist)
class ItemAdmin(admin.ModelAdmin):
    list_display = ("codigo", "descripcion", "ambito", "obligatorio")
    list_filter = ("seccion", "ambito", "obligatorio")


@admin.register(Ciclo)
class CicloAdmin(admin.ModelAdmin):
    list_display = ("__str__", "fecha_inicio", "fecha_termino")


@admin.register(Visita)
class VisitaAdmin(admin.ModelAdmin):
    list_display = ("local", "ciclo", "fecha", "estado", "porcentaje_cobertura")
    list_filter = ("estado", "ciclo", "local")
    filter_horizontal = ("cuadrilla",)
    readonly_fields = ("cerrada_por", "ts_cierre")


admin.site.register(RegistroTablero, SoloLectura)
admin.site.register(RegistroItem, SoloLectura)
admin.site.register(Evidencia, SoloLectura)
admin.site.register(Observacion, SoloLectura)
admin.site.register(Hallazgo, SoloLectura)
admin.site.register(Pendiente, SoloLectura)
admin.site.register(MedicionElectrica, SoloLectura)
admin.site.register(MaterialFaltante, SoloLectura)
admin.site.register(InformeVisita, SoloLectura)
admin.site.register(LibroAnual, SoloLectura)

admin.site.site_header = "SIG IMELSE — Administración"
admin.site.site_title = "SIG IMELSE"
admin.site.index_title = "Catálogo maestro y consulta de registros"
