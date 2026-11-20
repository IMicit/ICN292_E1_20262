"""
Configuración del SIG IMELSE.

Motor de base de datos
----------------------
Producción declarada: PostgreSQL 16. El esquema y los datos se verificaron
sobre 16.15.
Prototipo de la Entrega 2: SQLite 3, para cumplir RNF-09 (reproducible en
localhost desde el repositorio, sin instalar un servidor de base de datos).

El cambio entre ambos es una variable de entorno, no un cambio de código:

    export DATABASE_URL=postgresql://usuario:clave@localhost:5432/sig_imelse

Sin esa variable, el proyecto usa SQLite y arranca con `python manage.py runserver`.
"""

import os
from pathlib import Path
from urllib.parse import urlparse

BASE_DIR = Path(__file__).resolve().parent.parent

SECRET_KEY = os.environ.get(
    "DJANGO_SECRET_KEY", "prototipo-icn292-no-usar-en-produccion"
)
DEBUG = os.environ.get("DJANGO_DEBUG", "1") == "1"
ALLOWED_HOSTS = ["*"]

INSTALLED_APPS = [
    "django.contrib.admin",
    "django.contrib.auth",
    "django.contrib.contenttypes",
    "django.contrib.sessions",
    "django.contrib.messages",
    "django.contrib.staticfiles",
    "core",
]

MIDDLEWARE = [
    "django.middleware.security.SecurityMiddleware",
    "django.contrib.sessions.middleware.SessionMiddleware",
    "django.middleware.common.CommonMiddleware",
    "django.middleware.csrf.CsrfViewMiddleware",
    "django.contrib.auth.middleware.AuthenticationMiddleware",
    "django.contrib.messages.middleware.MessageMiddleware",
    "django.middleware.clickjacking.XFrameOptionsMiddleware",
]

ROOT_URLCONF = "config.urls"

TEMPLATES = [
    {
        "BACKEND": "django.template.backends.django.DjangoTemplates",
        "DIRS": [BASE_DIR / "core" / "templates"],
        "APP_DIRS": True,
        "OPTIONS": {
            "context_processors": [
                "django.template.context_processors.request",
                "django.contrib.auth.context_processors.auth",
                "django.contrib.messages.context_processors.messages",
            ],
        },
    },
]

WSGI_APPLICATION = "config.wsgi.application"


# --- Base de datos ---------------------------------------------------------

_url = os.environ.get("DATABASE_URL")
if _url:
    _p = urlparse(_url)
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.postgresql",
            "NAME": _p.path.lstrip("/"),
            "USER": _p.username or "",
            "PASSWORD": _p.password or "",
            "HOST": _p.hostname or "localhost",
            "PORT": str(_p.port or 5432),
        }
    }
else:
    DATABASES = {
        "default": {
            "ENGINE": "django.db.backends.sqlite3",
            "NAME": BASE_DIR / "db.sqlite3",
        }
    }


AUTH_USER_MODEL = "core.Usuario"

AUTH_PASSWORD_VALIDATORS = [
    {"NAME": "django.contrib.auth.password_validation.CommonPasswordValidator"},
    {"NAME": "django.contrib.auth.password_validation.MinimumLengthValidator"},
]

LOGIN_URL = "login"
LOGIN_REDIRECT_URL = "inicio"
LOGOUT_REDIRECT_URL = "login"

LANGUAGE_CODE = "es-cl"
TIME_ZONE = "America/Santiago"
USE_I18N = True
USE_TZ = True

STATIC_URL = "static/"
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = "media/"
MEDIA_ROOT = BASE_DIR / "media"

DEFAULT_AUTO_FIELD = "django.db.models.BigAutoField"


# --- Parámetros del dominio (métricas de los RNF) --------------------------
# Se declaran aquí, con número y unidad, para que sean verificables en el
# código y no sólo en el informe.

EVIDENCIA_MAX_LADO_PX = 1600      # RNF-08: lado largo tras compresión
EVIDENCIA_CALIDAD_JPEG = 80       # RNF-08: calidad de recompresión
EVIDENCIA_MAX_BYTES = 500 * 1024  # RNF-08: 500 KB por fotografía

# RF-03/RF-04: antigüedad máxima admitida de una fotografía, en segundos.
# Una imagen cuyo archivo es más viejo que esto no se acepta: la evidencia se
# captura durante la ejecución, no se adjunta después desde la galería.
EVIDENCIA_MAX_ANTIGUEDAD_S = 15 * 60

# --- Integración con la automatización (n8n) -------------------------------
# El SIG anuncia hechos de negocio y deja que la automatización decida qué
# hacer con ellos. Si estas variables están vacías, el sistema funciona igual:
# simplemente no avisa hacia afuera.

N8N_WEBHOOK_URL = os.environ.get("N8N_WEBHOOK_URL", "")
SIG_API_TOKEN = os.environ.get("SIG_API_TOKEN", "sig-imelse-token-de-demostracion")
SIG_BASE_URL = os.environ.get("SIG_BASE_URL", "http://127.0.0.1:8000")
SIG_CORREO_CLIENTE = os.environ.get("SIG_CORREO_CLIENTE", "contacto@cliente-demo.cl")
SIG_CORREO_GERENCIA = os.environ.get("SIG_CORREO_GERENCIA", "gerencia@imelse-demo.cl")


# RNF-01: operación sin conexión.
OFFLINE_MAX_HORAS = 8             # captura local admitida sin red
OFFLINE_MAX_SINC_S = 60           # tope de sincronización al recuperar señal
