import base64
import json
import os
import requests
import struct
import uuid
import wave

BASE_URL = "http://127.0.0.1:8000/api"
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
ASSET_DIR = os.path.join(ROOT, "backend", "static", "assets")
os.makedirs(ASSET_DIR, exist_ok=True)

image_path = os.path.join(ASSET_DIR, f"e2e_image_{uuid.uuid4().hex}.png")
audio_path = os.path.join(ASSET_DIR, f"e2e_audio_{uuid.uuid4().hex}.wav")
png_bytes = base64.b64decode(
    "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=="
)
with open(image_path, "wb") as f:
    f.write(png_bytes)

with wave.open(audio_path, "wb") as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(22050)
    frames = struct.pack("<" + "h" * 22050, *([0] * 22050))
    wav_file.writeframes(frames)

print("Created image:", image_path)
print("Created audio:", audio_path)

script_resp = requests.post(
    f"{BASE_URL}/scripts",
    json={"title": "E2E Script", "description": "E2E test script"},
)
script_resp.raise_for_status()
script = script_resp.json()
print("Created script:", script["id"])

scene_resp = requests.post(
    f"{BASE_URL}/scenes",
    json={
        "script_id": script["id"],
        "title": "E2E Scene",
        "description": "E2E scene",
        "image_path": image_path,
        "audio_path": audio_path,
        "style": "cinematic",
        "duration_seconds": 2,
    },
)
scene_resp.raise_for_status()
scene = scene_resp.json()
print("Created scene:", scene["id"])

video_resp = requests.post(f"{BASE_URL}/scenes/{scene['id']}/generate-video")
print("Generate-video status:", video_resp.status_code)
try:
    print(json.dumps(video_resp.json(), indent=2))
except Exception:
    print(video_resp.text)

scene_check = requests.get(f"{BASE_URL}/scenes/{scene['id']}")
scene_check.raise_for_status()
print("Scene after generation:", json.dumps(scene_check.json(), indent=2))

print("Frontend render URL:", f"http://127.0.0.1:3000/render/{script['id']}")
