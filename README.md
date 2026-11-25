# Semana 13: API RESTful con Django REST Framework

Práctica del Laboratorio 13 de Desarrollo de Aplicaciones Web (UNCP). Implementa una API de catálogo de recursos con DRF, serialización e hipervínculos HATEOAS, ViewSets y routers, filtros, paginación, throttling, permisos, CORS/CSRF y documentación OpenAPI.

## Requisitos

- Python 3.11 o superior
- Git (opcional, para publicar el proyecto)
- PowerShell en Windows o una terminal compatible

La base de datos SQLite se crea localmente al ejecutar las migraciones. No se incluyen credenciales ni datos de desarrollo.

## Instalación en Windows (PowerShell)

Desde la carpeta del proyecto:

```powershell
py -3 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
python manage.py migrate
python manage.py check
```

Si PowerShell impide activar el entorno, ejecuta `Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass` en esa terminal y vuelve a activar `.venv`. También puedes omitir la activación y usar `.\.venv\Scripts\python.exe` en los comandos.

En Linux/macOS, sustituye la activación por `source .venv/bin/activate`.

## Ejecutar y probar

Inicia el servidor:

```powershell
python manage.py runserver
```

En otra terminal, ejecuta las pruebas automatizadas:

```powershell
python manage.py test
```

La suite verifica CRUD/permisos, validación, hipervínculos, resumen, filtrado, búsqueda, límite de paginación, CSRF, CORS, esquema OpenAPI y throttling.

### Rutas principales

| Método | Ruta | Descripción |
|---|---|---|
| GET, POST | `/api/recursos/` | Listar y crear recursos |
| GET, PUT, PATCH, DELETE | `/api/recursos/{id}/` | Consultar, actualizar y eliminar un recurso |
| POST | `/api/recursos/{id}/activar/` | Activar un recurso |
| GET | `/api/recursos/resumen/` | Estado y total de recursos |
| GET | `/api/csrf/` | Preparar la cookie CSRF para clientes SPA |
| GET | `/api/schema/` | Esquema OpenAPI |
| GET | `/api/docs/` | Interfaz Swagger UI |
| GET | `/api/redoc/` | Documentación ReDoc |
| GET | `/api/auth/login/` | Inicio de sesión para la API navegable |
| GET | `/admin/` | Administración de Django |

Las lecturas son públicas. Para crear, actualizar, activar o eliminar, inicia sesión; solo el propietario puede modificar su recurso. La autenticación admite sesión y HTTP Basic. Con sesión, las peticiones que modifican datos requieren CSRF.

### Consultas de ejemplo

```text
http://127.0.0.1:8000/api/recursos/?status=active&category=equipos
http://127.0.0.1:8000/api/recursos/?search=equipo&ordering=name
http://127.0.0.1:8000/api/recursos/?page=2&page_size=20
http://127.0.0.1:8000/api/recursos/resumen/
```

La respuesta de colección está paginada (`count`, `next`, `previous`, `results`). El tamaño predeterminado es 10 y `page_size` está limitado a 50. Los clientes anónimos tienen un máximo de 20 solicitudes por minuto; los usuarios autenticados, 100 por minuto.

### Crear datos para probar

Crea un usuario administrador y sigue las instrucciones interactivas:

```powershell
python manage.py createsuperuser
```

Inicia sesión en `http://127.0.0.1:8000/admin/` y crea uno o varios recursos. También puedes iniciar sesión en `/api/auth/login/` para usar la interfaz navegable de DRF.

Para comprobar CORS desde un frontend autorizado, los orígenes permitidos por defecto son `http://localhost:3000` y `http://127.0.0.1:5500`. Una petición de preflight de ejemplo:

```powershell
curl.exe -i -X OPTIONS http://127.0.0.1:8000/api/recursos/ `
  -H "Origin: http://localhost:3000" `
  -H "Access-Control-Request-Method: POST" `
  -H "Access-Control-Request-Headers: Content-Type, X-CSRFToken"
```

Para un cliente SPA, solicita primero `/api/csrf/` con credenciales, conserva la cookie `csrftoken` y envía su valor en `X-CSRFToken` en cada `POST`, `PUT`, `PATCH` o `DELETE`. No desactives la protección CSRF.

## Configuración

Los valores predeterminados son para desarrollo local. Se pueden definir estas variables de entorno antes de iniciar Django:

| Variable | Uso |
|---|---|
| `DJANGO_SECRET_KEY` | Clave secreta (obligatoria y segura fuera de desarrollo) |
| `DJANGO_DEBUG` | `true` para desarrollo; configura `false` en despliegues |
| `DJANGO_ALLOWED_HOSTS` | Hosts separados por coma |
| `CORS_ALLOWED_ORIGINS` | Orígenes CORS separados por coma; no se permite `*` |
| `CSRF_TRUSTED_ORIGINS` | Orígenes confiables CSRF separados por coma |

Ejemplo PowerShell:

```powershell
$env:CORS_ALLOWED_ORIGINS = "http://localhost:3000"
$env:CSRF_TRUSTED_ORIGINS = "http://localhost:3000"
$env:DJANGO_DEBUG = "true"
```

No publiques secretos, `.env`, `.venv` ni `db.sqlite3`. Para un despliegue, configura una clave secreta real, `DEBUG=false`, hosts y orígenes explícitos, y utiliza un servidor WSGI/ASGI apropiado.

## Estructura

```text
config/             Configuración Django, middleware y rutas
api/models.py       Modelo Resource e índices/constraint
api/serializers.py  Serialización hipervinculada y datos de estado
api/views.py        ModelViewSet, acciones y cookie CSRF
api/permissions.py  Lectura pública y escritura por propietario
api/pagination.py   Paginación de 10, máximo 50
api/tests.py        Pruebas automatizadas de API e integración
requirements.txt    Dependencias del proyecto
```


## Publicar en GitHub

El proyecto no crea commits ni repositorios remotos. Cuando hayas revisado las pruebas, crea un repositorio vacío en tu cuenta y ejecuta desde esta carpeta:

```powershell
git init
git add .
git commit -m "Completa practica de API RESTful - Semana 13"
git branch -M main
git remote add origin https://github.com/TU_USUARIO/TU_REPOSITORIO.git
git push -u origin main
```
