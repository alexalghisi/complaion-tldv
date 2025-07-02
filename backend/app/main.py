"""
Entry point dell'applicazione FastAPI
"""

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.responses import JSONResponse
import logging
import time
from contextlib import asynccontextmanager

from .core.config import settings
from .core.firebase import firebase_service

# Configurazione logging
logging.basicConfig(
    level=getattr(logging, settings.log_level.upper()),
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(settings.log_file) if settings.log_file else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestione del ciclo di vita dell'applicazione"""
    logger.info("🚀 Avvio applicazione tl;dv Integration")

    # Inizializzazione Firebase
    try:
        firebase_service.db.collection('_health').document('startup').set({
            'timestamp': time.time(),
            'status': 'started'
        })
        logger.info("✅ Firebase inizializzato correttamente")
    except Exception as e:
        logger.error(f"❌ Errore inizializzazione Firebase: {e}")

    yield

    logger.info("🛑 Chiusura applicazione")

# Creazione app FastAPI
app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description="API per l'integrazione con tl;dv per il download e gestione di meetings",
    docs_url="/docs" if settings.debug else None,
    redoc_url="/redoc" if settings.debug else None,
    lifespan=lifespan
)

# Middleware CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Middleware per host fidati
app.add_middleware(
    TrustedHostMiddleware,
    allowed_hosts=["*"] if settings.debug else ["localhost", "127.0.0.1"]
)

# Middleware per logging delle richieste
@app.middleware("http")
async def log_requests(request: Request, call_next):
    """Log delle richieste HTTP"""
    start_time = time.time()

    response = await call_next(request)

    process_time = time.time() - start_time
    logger.info(
        f"{request.method} {request.url.path} - "
        f"Status: {response.status_code} - "
        f"Time: {process_time:.3f}s"
    )

    return response

# Health check endpoint
@app.get("/health")
async def health_check():
    """Health check dell'applicazione"""
    try:
        # Test connessione Firebase
        firebase_service.db.collection('_health').document('check').set({
            'timestamp': time.time(),
            'status': 'healthy'
        })

        return {
            "status": "healthy",
            "version": settings.app_version,
            "environment": settings.environment,
            "firebase": "connected"
        }
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "status": "unhealthy",
                "error": str(e)
            }
        )

# Root endpoint
@app.get("/")
async def root():
    """Endpoint root"""
    return {
        "message": "tl;dv Integration API",
        "version": settings.app_version,
        "docs": "/docs" if settings.debug else "Documentation not available in production"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.api_host,
        port=settings.api_port,
        reload=settings.debug,
        log_level=settings.log_level.lower()
    )