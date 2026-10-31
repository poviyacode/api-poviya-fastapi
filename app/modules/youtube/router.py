import httpx
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.modules.youtube.schemas import URLRequest
from app.modules.youtube.service import YouTubeService

router = APIRouter(prefix="/api/youtube", tags=["YouTube"])


@router.post("/extract")
async def extract_video(request: URLRequest):
    return await YouTubeService.extract_info(request.url)


@router.get("/download")
async def proxy_download(video_url: str = Query(...)):
    from urllib.parse import urlparse

    # Dominios permitidos según la plataforma
    allowed_domains = [
        "googlevideo.com",
        "youtube.com",
        "youtu.be",
        "ggpht.com",
    ]  # Cambiar para TikTok

    parsed = urlparse(video_url)
    if not any(domain in parsed.netloc for domain in allowed_domains):
        raise HTTPException(status_code=400, detail="URL no permitida")

    try:
        with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Referer": "https://www.youtube.com/",  # O tiktok.com
            }

            response = client.get(video_url, headers=headers)
            response.raise_for_status()

            # Obtener nombre de archivo real si el servidor lo envía
            filename = "video_descargado.mp4"
            content_disp = response.headers.get("Content-Disposition", "")
            if "filename=" in content_disp:
                filename = content_disp.split("filename=")[-1].strip('"')

            return StreamingResponse(
                iter([response.content]),
                media_type="video/mp4",
                headers={
                    "Content-Disposition": f'attachment; filename="{filename}"',
                    "Content-Length": str(len(response.content)),
                },
            )
    except httpx.HTTPStatusError as e:
        raise HTTPException(
            status_code=502,
            detail=f"Error del servidor de video: {e.response.status_code}",
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error interno: {str(e)}")
