import httpx
from urllib.parse import urlparse
from fastapi import APIRouter, HTTPException, Query
from fastapi.responses import StreamingResponse
from app.modules.tiktok.schemas import URLRequest
from app.modules.tiktok.service import TikTokService

router = APIRouter(prefix="/api/tiktok", tags=["TikTok"])


@router.post("/extract")
async def extract_video(request: URLRequest):
    return await TikTokService.extract_info(request.url)


@router.get("/download")
async def proxy_download(video_url: str = Query(...)):
    from urllib.parse import urlparse
    import logging

    logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)

    # Dominios de TikTok
    allowed_domains = [
        "tiktok.com",
        "tiktokcdn.com",
        "tiktokcdn-us.com",
        "byteoversea.com",
        "musical.ly",
        "amazonaws.com",  # Algunos videos se sirven desde AWS
    ]

    parsed = urlparse(video_url)

    if not any(domain in parsed.netloc for domain in allowed_domains):
        raise HTTPException(status_code=400, detail="URL no permitida")

    try:
        logger.info(f"Descargando desde TikTok: {parsed.netloc}")

        with httpx.Client(timeout=httpx.Timeout(120.0)) as client:
            # Headers más completos para TikTok
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "*/*",
                "Accept-Encoding": "identity",  # Importante: sin compresión
                "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
                "Referer": "https://www.tiktok.com/",
                "Origin": "https://www.tiktok.com",
                "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120"',
                "Sec-Ch-Ua-Mobile": "?0",
                "Sec-Ch-Ua-Platform": '"Windows"',
            }

            logger.info(f"Headers enviados: {headers['User-Agent']}")

            response = client.get(video_url, headers=headers, follow_redirects=True)

            logger.info(f"Status code: {response.status_code}")
            logger.info(f"Content-Type: {response.headers.get('Content-Type')}")

            response.raise_for_status()

            # Verificar que sea un video
            content_type = response.headers.get("Content-Type", "")
            if "video" not in content_type and len(response.content) < 1000:
                logger.warning(
                    f"Posible error: Content-Type={content_type}, Size={len(response.content)}"
                )
                # No es un video o es muy pequeño

            filename = "video_tiktok.mp4"
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
        logger.error(f"HTTP Error {e.response.status_code}: {e.response.text[:200]}")
        raise HTTPException(
            status_code=502,
            detail=f"TikTok respondió con error {e.response.status_code}",
        )
    except httpx.ConnectError as e:
        logger.error(f"Connection Error: {str(e)}")
        raise HTTPException(status_code=502, detail="No se pudo conectar con TikTok")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error: {str(e)}")
