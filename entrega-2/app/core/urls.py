from django.contrib.auth import views as auth_views
from django.urls import path

from . import api, views

urlpatterns = [
    path("", views.inicio, name="inicio"),

    # El service worker sólo controla rutas a su propio nivel o por debajo, así
    # que tiene que servirse desde la raíz y no desde /static/ (RNF-01).
    path("sw.js", views.service_worker, name="sw"),
    path("manifest.json", views.manifiesto, name="manifiesto"),
    path("entrar/", auth_views.LoginView.as_view(template_name="core/login.html"), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),

    # Terreno
    path("visitas/", views.visitas, name="visitas"),
    path("visitas/<int:pk>/", views.visita_detalle, name="visita_detalle"),
    path("visitas/<int:pk>/pauta/", views.visita_items, name="visita_items"),
    path("visitas/<int:pk>/cerrar/", views.cerrar_visita, name="cerrar_visita"),
    path(
        "visitas/<int:visita_pk>/tablero/<int:tablero_pk>/",
        views.tablero_registro,
        name="tablero_registro",
    ),
    path(
        "visitas/<int:visita_pk>/tablero/<int:tablero_pk>/pendiente/",
        views.declarar_pendiente,
        name="declarar_pendiente",
    ),
    path("visitas/<int:pk>/materiales/", views.visita_materiales, name="visita_materiales"),

    # Oficina
    path("panel/", views.panel, name="panel"),
    path("ciclos/", views.ciclos, name="ciclos"),
    path("materiales/", views.materiales, name="materiales"),
    path("locales/", views.locales, name="locales"),
    path("consultas/", views.consultas_sql, name="consultas_sql"),
    path("planilla/", views.libro_anual, name="libro_anual"),
    path("planilla/<int:anio>/descargar/", views.descargar_libro, name="descargar_libro"),
    path("informe/<int:pk>/", views.informe_visita, name="informe_visita"),
    path("informe/<int:pk>/archivo/", views.informes_visita, name="informes_visita"),
    path("informe/descargar/<int:pk>/", views.descargar_informe, name="descargar_informe"),
    path("tablero/<int:pk>/historial/", views.historial_tablero, name="historial_tablero"),

    # API para la automatización (n8n)
    path("api/informe/<int:pk>/pdf/", api.informe_pdf, name="api_informe_pdf"),
    path("api/informe/<int:pk>/despacho/", api.informe_despacho, name="api_informe_despacho"),
]
