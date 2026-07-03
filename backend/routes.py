import os
import uuid
from pathlib import Path
from typing import List
from urllib.parse import quote

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import FileResponse

from backend.data_store import render_tasks, scenes, scripts
from backend.models import (
    RenderRequest,
    RenderTask,
    Scene,
    SceneCreate,
    SceneUpdate,
    Script,
    ScriptCreate,
    ScriptResponse,
)
from workers.video_generator import generate_video_with_model
from workers.exceptions import VideoGenerationError

router = APIRouter()

BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"
VIDEO_DIR = STATIC_DIR / "videos"
VIDEO_DIR.mkdir(parents=True, exist_ok=True)

PLACEHOLDER_IMAGE_SVG = "<svg xmlns='http://www.w3.org/2000/svg' width='640' height='360'><rect width='100%' height='100%' fill='%23ddd'/><text x='50%' y='50%' dominant-baseline='middle' text-anchor='middle' fill='%23666' font-size='24'>Placeholder Image</text></svg>"
PLACEHOLDER_IMAGE_URL = f"data:image/svg+xml;utf8,{quote(PLACEHOLDER_IMAGE_SVG)}"
PLACEHOLDER_AUDIO_URL = "https://interactive-examples.mdn.mozilla.net/media/examples/t-rex-roar.mp3"


@router.get("/health")
def health() -> dict:
    return {"status": "ok"}


@router.get("/scripts/{script_id}", response_model=ScriptResponse)
def get_script(script_id: str) -> ScriptResponse:
    script = scripts.get(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    script_scenes = [scene for scene in scenes.values() if scene.script_id == script_id]
    return ScriptResponse(script=script, scenes=script_scenes)


@router.post("/scripts", response_model=Script)
def create_script(script_in: ScriptCreate) -> Script:
    script_id = str(uuid.uuid4())
    script = Script(id=script_id, title=script_in.title, description=script_in.description, settings={})
    scripts[script_id] = script
    return script


@router.patch("/scripts/{script_id}", response_model=Script)
def update_script(script_id: str, updates: dict) -> Script:
    script = scripts.get(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    # allow updating title, description, and settings
    title = updates.get("title", script.title)
    description = updates.get("description", script.description)
    settings = updates.get("settings", script.settings or {})

    updated = Script(id=script.id, title=title, description=description, settings=settings)
    scripts[script_id] = updated
    return updated


@router.get("/scripts", response_model=List[Script])
def list_scripts() -> List[Script]:
    return list(scripts.values())


@router.get("/scenes", response_model=List[Scene])
def list_scenes() -> List[Scene]:
    return list(scenes.values())


@router.post("/scenes", response_model=Scene)
def create_scene(scene_in: SceneCreate) -> Scene:
    scene_id = str(uuid.uuid4())
    scene = Scene(
        id=scene_id,
        script_id=scene_in.script_id,
        title=scene_in.title,
        description=scene_in.description,
        image_path=scene_in.image_path,
        audio_path=scene_in.audio_path,
        style=scene_in.style,
        duration_seconds=scene_in.duration_seconds,
    )
    scenes[scene_id] = scene
    return scene


@router.patch("/scenes/{scene_id}", response_model=Scene)
def update_scene(scene_id: str, scene_update: SceneUpdate) -> Scene:
    scene = scenes.get(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    updated_scene = scene.model_copy(update=scene_update.model_dump(exclude_unset=True))
    scenes[scene_id] = updated_scene
    return updated_scene


@router.get("/scenes/{scene_id}", response_model=Scene)
def get_scene(scene_id: str) -> Scene:
    scene = scenes.get(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")
    return scene


@router.post("/scenes/{scene_id}/generate-image")
def generate_scene_image(scene_id: str, request: Request) -> dict:
    scene = scenes.get(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene.image_url = scene.image_path if scene.image_path.startswith("http") else PLACEHOLDER_IMAGE_URL
    scenes[scene_id] = scene
    return {"scene_id": scene_id, "image_url": scene.image_url}


@router.post("/scenes/{scene_id}/generate-voice")
def generate_scene_voice(scene_id: str, request: Request) -> dict:
    scene = scenes.get(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    scene.voice_audio_url = scene.audio_path if scene.audio_path.startswith("http") else PLACEHOLDER_AUDIO_URL
    scenes[scene_id] = scene
    return {"scene_id": scene_id, "voice_audio_url": scene.voice_audio_url}


@router.post("/scenes/{scene_id}/generate-video")
def generate_scene_video(scene_id: str, request: Request) -> dict:
    scene = scenes.get(scene_id)
    if not scene:
        raise HTTPException(status_code=404, detail="Scene not found")

    if not os.path.exists(scene.image_path):
        raise HTTPException(status_code=400, detail="Image path does not exist")
    if not os.path.exists(scene.audio_path):
        raise HTTPException(status_code=400, detail="Audio path does not exist")

    filename = f"{scene_id}.mp4"
    output_path = VIDEO_DIR / filename

    try:
        generate_video_with_model(
            image_path=scene.image_path,
            audio_path=scene.audio_path,
            style=scene.style,
            duration=scene.duration_seconds,
            output_path=str(output_path),
        )
    except VideoGenerationError as exc:
        raise HTTPException(status_code=500, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Unexpected error: {exc}")

    scene.video_url = str(request.url_for("serve_video", filename=filename))
    scenes[scene_id] = scene
    return {"job_id": scene_id, "video_url": scene.video_url}


@router.post("/render/{script_id}")
def start_render(script_id: str, settings: RenderRequest) -> dict:
    script = scripts.get(script_id)
    if not script:
        raise HTTPException(status_code=404, detail="Script not found")

    render_id = str(uuid.uuid4())
    script_scenes = [scene for scene in scenes.values() if scene.script_id == script_id]
    final_video_url = next((scene.video_url for scene in script_scenes if scene.video_url), None)
    status = "done" if final_video_url else "processing"

    # Resolve AI-powered "choose" placeholders into concrete defaults.
    resolved = settings.model_dump()
    defaults = {
        "niche": "Social media ads",
        "language_voice": "English - Female",
        "background_music": "Cinematic",
        "art_style": "Cinematic",
        "caption_style": "Modern captions",
        "effects": "None",
    }

    for key, default_val in defaults.items():
        val = resolved.get(key)
        if isinstance(val, str) and (val.strip() == "" or val.strip().lower().startswith("ai") or "choose" in val.lower()):
            resolved[key] = default_val

    try:
        resolved["duration_seconds"] = int(resolved.get("duration_seconds", 60) or 60)
    except Exception:
        resolved["duration_seconds"] = 60

    # Apply simple heuristics to improve AI defaults based on script title or chosen niche.
    title = (script.title or "").lower()
    niche_val = (resolved.get("niche") or "").lower()

    # Heuristic rules
    if "tutorial" in title or "how to" in title or "education" in niche_val:
        resolved["art_style"] = "Minimal"
        resolved["background_music"] = "Ambient"
        resolved["caption_style"] = "Minimal subtitles"

    if "product" in title or "launch" in title or "product" in niche_val:
        resolved["background_music"] = "Upbeat"
        resolved["art_style"] = "Cinematic"

    if "horror" in title or "scary" in niche_val or resolved.get("effects", "").lower().find("glitch") != -1:
        resolved["effects"] = "Glitch"
        resolved["background_music"] = "Ambient"
        resolved["art_style"] = "Retro"

    # If user explicitly selected an art style or music, keep it (already handled above)

    render_task = RenderTask(
        id=render_id,
        script_id=script_id,
        status=status,
        final_video_url=final_video_url,
        settings=resolved,
    )
    render_tasks[render_id] = render_task

    return {
        "render_id": render_id,
        "status": status,
        "final_video_url": final_video_url,
        "settings": resolved,
    }


@router.get("/render/{render_id}")
def get_render_status(render_id: str) -> RenderTask:
    task = render_tasks.get(render_id)
    if not task:
        raise HTTPException(status_code=404, detail="Render task not found")
    return task


@router.get("/assets/videos/{filename}")
def serve_video(filename: str) -> FileResponse:
    path = VIDEO_DIR / filename
    if not path.exists():
        raise HTTPException(status_code=404, detail="Video not found")
    return FileResponse(path, media_type="video/mp4")



