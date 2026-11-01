from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.modules.instagram.router import router as instagram_router
from app.modules.youtube.router import router as youtube_router  # <-- NUEVO
from app.modules.tiktok.router import router as tiktok_router

app = FastAPI(title="Universal Downloader API fastapi.poviya.com", version="1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "*"
    ],  # Recomendación: Cambiar a ["http://localhost:3000"] en producción
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Registrar rutas de los módulos
app.include_router(instagram_router)
app.include_router(youtube_router)  # <-- NUEVO
app.include_router(tiktok_router)

@app.get("/")
async def root():
    return {
        "message": "API de Descarga activa.",
        "endpoints": [
            "POST /api/extract (Instagram)",
            "POST /api/youtube/extract (YouTube)",
            "POST /api/tiktok/extract (TikTok)",
            "GET /api/download (Proxy Instagram)",
            "GET /api/youtube/download (Proxy YouTube)",
            "GET /api/tiktok/download (Proxy TikTok)",
        ],
    }
