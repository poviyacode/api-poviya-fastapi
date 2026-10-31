import re
import yt_dlp
from fastapi import HTTPException


class InstagramService:
    @staticmethod
    def is_valid_url(url: str) -> bool:
        regex = re.compile(r"^(https?://)?(www\.)?(instagram\.com|instagr\.am)/.*$")
        return bool(regex.match(url))

    @staticmethod
    async def extract_info(url: str):
        if not InstagramService.is_valid_url(url):
            raise HTTPException(
                status_code=400,
                detail="La URL proporcionada no es válida o no pertenece a Instagram.",
            )

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            "extract_flat": False,
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36...",
                "Accept-Language": "en-us,en;q=0.5",
            },
        }

        try:
            with yt_dlp.YoutubeDL(ydl_opts) as ydl:
                info = ydl.extract_info(url, download=False)

                formats = []
                if "formats" in info:
                    for f in info["formats"]:
                        if f.get("url") and f.get("ext") in ["mp4", "webm"]:
                            formats.append(
                                {
                                    "format_id": f.get("format_id"),
                                    "ext": f.get("ext"),
                                    "resolution": f.get("resolution", "Desconocida"),
                                    "filesize": f.get("filesize"),
                                    "url": f.get("url"),
                                }
                            )

                if not formats and info.get("url"):
                    formats.append(
                        {
                            "format_id": "default",
                            "ext": info.get("ext", "mp4"),
                            "resolution": "Default",
                            "url": info.get("url"),
                        }
                    )

                return {
                    "success": True,
                    "title": info.get("title", "Video de Instagram"),
                    "thumbnail": info.get("thumbnail"),
                    "author": info.get("uploader", "Desconocido"),
                    "download_url": info.get("url"),  # ← AGREGAR ESTO
                    "formats": formats,
                }
        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            if "Private" in error_msg or "login" in error_msg:
                raise HTTPException(
                    status_code=403,
                    detail="El video es privado o requiere inicio de sesión.",
                )
            raise HTTPException(
                status_code=400, detail=f"Error al extraer el video: {error_msg}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error interno del servidor: {str(e)}"
            )
