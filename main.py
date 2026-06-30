import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from database import engine, Base
from routes import api

# --- CONFIGURACIÓN DE AUDITORÍA (LOGS) ---
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)
logger = logging.getLogger("ERP_MASTER")


# --- MANEJO DEL CICLO DE VIDA (LIFESPAN) ---
@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Controla qué pasa cuando el ERP se enciende y se apaga de forma segura.
    Reemplaza los antiguos eventos obsoletos @app.on_event('startup').
    """
    logger.info("🚀 Iniciando el motor del ERP Resinas Epóxicas...")
    try:
        logger.info("📦 Verificando consistencia de la Base de Datos y creando tablas...")
        Base.metadata.create_all(bind=engine)
        logger.info("✅ Base de datos lista para operar.")
    except Exception as e:
        logger.critical(f"❌ Error fatal al inicializar la base de datos: {str(e)}")
        raise e

    yield  # Aquí es donde la aplicación se queda corriendo atendiendo peticiones

    logger.info("🛑 Apagando el servidor ERP de forma segura...")


# --- INICIALIZACIÓN DE FASTAPI ---
app = FastAPI(
    title="ERP Resinas Epóxicas MVP",
    description="Sistema centralizado para la gestión de inventarios, combos y procesamiento ACID de ventas.",
    version="1.0.0",
    lifespan=lifespan
)

# --- MIDDLEWARE: SEGURIDAD Y CORS ---
# Permite que el sistema sea escalable si decides separar el frontend a otro servidor o conectar una App móvil
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # En producción reemplázalo por tu dominio específico
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# --- CONTROLADOR GLOBAL DE ERRORES NO CAPTURADOS ---
@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    """
    Cazador de errores de última instancia. Evita que el servidor muera
    y le responde al frontend siempre en formato JSON limpio.
    """
    logger.error(f"💥 Error crítico no controlado en {request.url.path}: {str(exc)}", exc_info=True)
    return JSONResponse(
        status_code=500,
        content={
            "status": "error",
            "detail": "Ocurrió un error interno inesperado en el servidor ERP. Por favor, revise los logs del sistema."
        }
    )


# --- REGISTRO DE CAPAS (EL ORDEN IMPORTA) ---

# 1. Rutas de la API (Tienen prioridad absoluta de evaluación)
app.include_router(api.router, prefix="/api")

# 2. Frontend Estático (Se monta al final de todo para no canibalizar las rutas de la API)
app.mount("/", StaticFiles(directory="static", html=True), name="static")