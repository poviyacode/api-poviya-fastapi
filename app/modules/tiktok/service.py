import asyncio
import re
import os
from functools import partial
import yt_dlp
from fastapi import HTTPException


class TikTokService:
    @staticmethod
    def is_valid_url(url: str) -> bool:
        regex = re.compile(r"^(https?://)?(www\.|vm\.|vt\.)?tiktok\.com/.*$")
        return bool(regex.match(url))

    @staticmethod
    def _extract_sync(url: str, ydl_opts: dict):
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            return ydl.extract_info(url, download=False)

    @staticmethod
    async def extract_info(url: str):
        if not TikTokService.is_valid_url(url):
            raise HTTPException(
                status_code=400,
                detail="La URL proporcionada no es válida o no pertenece a TikTok.",
            )

        # Obtenemos la ruta absoluta al archivo de cookies
        # Asegúrate de que 'tiktok_cookies.txt' esté en la raíz de tu proyecto
        cookie_file = os.path.join(
            os.path.dirname(__file__), "../../../tiktok_cookies.txt"
        )

        # Si el archivo no existe, yt-dlp lo ignorará, pero es bueno tenerlo
        if not os.path.exists(cookie_file):
            cookie_file = None

        ydl_opts = {
            "quiet": True,
            "no_warnings": True,
            # Forzar formato sin marca de agua si está disponible
            "format": "best[ext=mp4]/best",
            "http_headers": {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept-Language": "en-US,en;q=0.9,es;q=0.8",
                "Referer": "https://www.tiktok.com/",
            },
        }

        try:
            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(
                None, partial(TikTokService._extract_sync, url, ydl_opts)
            )

            formats = []
            download_url = None
            if "formats" in info:
                for f in info["formats"]:
                    if f.get("format_id") == "download" and f.get("url"):
                        download_url = f.get("url")
                        break

                # Si no hay "download", usar el mejor disponible
                if not download_url:
                    for f in reversed(
                        info["formats"]
                    ):  # Revisar del último al primero (mejor calidad)
                        if (
                            f.get("url")
                            and f.get("ext") == "mp4"
                            and "watermarked"
                            not in str(f.get("resolution", "")).lower()
                        ):
                            download_url = f.get("url")
                            break

            return {
                "success": True,
                "title": info.get("title", "Video de TikTok"),
                "thumbnail": info.get("thumbnail"),
                "author": info.get("uploader", "Desconocido"),
                "download_url": download_url
                or info.get("url"),  # Usar el que encontramos
                "formats": formats,
            }

        except yt_dlp.utils.DownloadError as e:
            error_msg = str(e)
            # Manejo específico del error de TikTok
            if "status code 0" in error_msg or "Video not available" in error_msg:
                raise HTTPException(
                    status_code=403,
                    detail="TikTok bloqueó la solicitud. Asegúrate de que el video sea público y de haber actualizado yt-dlp y las cookies.",
                )
            if "private" in error_msg.lower() or "unavailable" in error_msg.lower():
                raise HTTPException(
                    status_code=404,
                    detail="El video es privado, fue eliminado o no está disponible.",
                )
            raise HTTPException(
                status_code=400, detail=f"Error al extraer el video: {error_msg}"
            )
        except Exception as e:
            raise HTTPException(
                status_code=500, detail=f"Error interno del servidor: {str(e)}"
            )
