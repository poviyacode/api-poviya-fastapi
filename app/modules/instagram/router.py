import httpx
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.modules.instagram.schemas import URLRequest
from app.modules.instagram.service import InstagramService

router = APIRouter(prefix="/api/instagram", tags=["Instagram"])


@router.post("/extract")
async def extract_video(request: URLRequest):
    return await InstagramService.extract_info(request.url)


@router.get("/download")
async def proxy_download(video_url: str = Query(...)):
    from urllib.parse import urlparse

    allowed_domains = ["instagram.com", "fbcdn.net", "facebook.com"]
    parsed = urlparse(video_url)

    if not any(domain in parsed.netloc for domain in allowed_domains):
        raise HTTPException(status_code=400, detail="URL no permitida")

    try:
        # Petición síncrona simple - lee todo el contenido
        with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
                "Referer": "https://www.instagram.com/",
            }

            response = client.get(video_url, headers=headers)
            response.raise_for_status()

            # Retornar todo el contenido de una vez
            return StreamingResponse(
                iter([response.content]),
                media_type="video/mp4",
                headers={
                    "Content-Disposition": 'attachment; filename="video_instagram.mp4"',
                    "Content-Length": str(len(response.content)),
                },
            )

    except httpx.HTTPStatusError as e:
        raise HTTPException(status_code=502, detail=f"Error {e.response.status_code}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
