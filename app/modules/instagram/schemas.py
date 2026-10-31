from pydantic import BaseModel
from typing import List, Optional


class URLRequest(BaseModel):
    url: str


class VideoFormat(BaseModel):
    format_id: str
    ext: str
    resolution: str
    filesize: Optional[int] = None
    url: str


class VideoExtractResponse(BaseModel):
    success: bool
    title: str
    thumbnail: Optional[str] = None
    author: str
    formats: List[VideoFormat]
