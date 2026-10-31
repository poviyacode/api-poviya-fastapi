import asyncio
import re
from functools import partial
import yt_dlp
from fastapi import HTTPException


class YouTubeService:
    @staticmethod
    def is_valid_url(url: str) -> bool:
        # Valida youtube.com, youtu.be, m.youtube.com, etc.
        regex = re.compile(r"^(https?://)?(www\.|m\.)?(youtube\.com|youtu\.be)/.*$")
        return bool(regex.match(url))

    @staticmethod
    def _extract_sync(url: str, ydl_opts: dict):
        """Método síncrono helper para ejecutar yt-dlp en un thread separado"""
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    @staticmethod
    async def extract_info(url: str):
        if not YouTubeService.is_valid_url(url):
            raise HTTPException(
                status_code=400,
                detail="La URL proporcionada no es válida o no pertenece a YouTube.",
            )

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            # 🎯 Cadena de formato robusta y profesional:
            # 1. Intenta unir video mp4 + audio m4a (requiere ffmpeg)
            # 2. Si no, busca un archivo mp4 pre-unido
            # 3. Si no, busca un archivo webm pre-unido
            # 4. Si no, descarga lo mejor que haya sin importar el formato
            "format": "bestvideo[ext=mp4]+bestaudio[ext=m4a]/best[ext=mp4]/best[ext=webm]/best",
            "merge_output_format": "mp4",  # Fuerza que el archivo final sea .mp4 si se unen
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
            },
        }

        try:
            loop = asyncio.get_event_loop()
            # ✅ EJECUCIÓN ASÍNCRONA REAL: No bloquea el event loop de FastAPI
            info = await loop.run_in_executor(
                None, partial(YouTubeService._extract_sync, url, ydl_opts)
            )

            formats = []
            if "formats" in info:
                for f in info["formats"]:
                    if f.get("url") and f.get("ext") in ["mp4", "webm", "m4a"]:
                        formats.append(
                            {
                                "format_id": str(f.get("format_id", "unknown")),
                                "ext": f.get("ext", "mp4"),
                                "resolution": f.get("resolution")
                                or f.get("format_note")
                                or "Desconocida",
                                "filesize": f.get("filesize"),
                                "url": f.get("url"),
                            }
                        )

            # Fallback si no se encontraron formatos en la lista pero sí una URL directa
            if not formats and info.get("url"):
                formats.append(
                    {
                        "format_id": "default",
                        "ext": info.get("ext", "mp4"),
                        "resolution": "Default",
                        "filesize": info.get("filesize"),
                        "url": info.get("url"),
                    }
                )

            return {
                "success": True,
                "title": info.get("title", "Video de YouTube"),
                "thumbnail": info.get("thumbnail"),
                "author": info.get("uploader", "Desconocido"),
                "formats": formats,
            }

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e).lower()
            if "private" in error_msg or "members-only" in error_msg:
                raise HTTPException(
                    status_code=403,
                    detail="El video es privado, solo para miembros o requiere inicio de sesión.",
                )
            raise HTTPException(
                status_code=400, detail=f"Error al extraer el video: {str(e)}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error interno del servidor: {str(e)}"
            )
