from pydantic import BaseModel
from typing import Any, Dict, List, Optional


class SceneCreate(BaseModel):
    title: str
    image_path: str
    audio_path: str
    description: Optional[str] = None
    style: str = "cinematic"
    duration_seconds: int = 10
    script_id: Optional[str] = None


class SceneUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    duration_seconds: Optional[int] = None
    style: Optional[str] = None


class Scene(BaseModel):
    id: str
    script_id: Optional[str]
    title: str
    description: Optional[str] = None
    image_path: str
    audio_path: str
    style: str
    duration_seconds: int
    image_url: Optional[str] = None
    voice_audio_url: Optional[str] = None
    video_url: Optional[str] = None


class ScriptCreate(BaseModel):
    title: str
    description: Optional[str] = None


class Script(BaseModel):
    id: str
    title: str
    description: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None


class ScriptResponse(BaseModel):
    script: Script
    scenes: List[Scene]


class RenderRequest(BaseModel):
    aspect_ratio: str = "9:16"
    resolution: str = "1080p"
    music_style: str = "cinematic"
    niche: Optional[str] = "Social media ads"
    language_voice: Optional[str] = "English - Female"
    background_music: Optional[str] = "Cinematic"
    art_style: Optional[str] = "Cinematic"
    caption_style: Optional[str] = "Modern captions"
    effects: Optional[str] = "None"
    social_accounts: Optional[str] = None
    duration_seconds: int = 60


class RenderTask(BaseModel):
    id: str
    script_id: str
    status: str
    final_video_url: Optional[str] = None
    settings: Optional[Dict[str, Any]] = None
