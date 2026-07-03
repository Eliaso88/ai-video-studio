import base64
import os
import requests
import uuid
import wave
import struct

BASE_URL = 'http://127.0.0.1:8000/api'
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
STATIC_DIR = os.path.join(ROOT, 'backend', 'static', 'assets')
os.makedirs(STATIC_DIR, exist_ok=True)

# minimal 1x1 PNG image
PNG_BYTES = base64.b64decode(
    'iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGMAAQAABQABDQottAAAAABJRU5ErkJggg=='
)
IMAGE_PATH = os.path.join(STATIC_DIR, f'test_image_{uuid.uuid4().hex}.png')
with open(IMAGE_PATH, 'wb') as f:
    f.write(PNG_BYTES)

# simple 1-second silent WAV
AUDIO_PATH = os.path.join(STATIC_DIR, f'test_audio_{uuid.uuid4().hex}.wav')
with wave.open(AUDIO_PATH, 'wb') as wav_file:
    wav_file.setnchannels(1)
    wav_file.setsampwidth(2)
    wav_file.setframerate(22050)
    frames = struct.pack('<' + 'h' * 22050, *([0] * 22050))
    wav_file.writeframes(frames)

print('Created image:', IMAGE_PATH)
print('Created audio:', AUDIO_PATH)

script_resp = requests.post(f'{BASE_URL}/scripts', json={'title': 'Test Video Script', 'description': 'Local assets for generate-video test'})
print('Script status:', script_resp.status_code, script_resp.text)
script_id = script_resp.json()['id']

scene_payload = {
    'title': 'Local Generate Video Scene',
    'description': 'Generated local image/audio assets',
    'image_path': IMAGE_PATH,
    'audio_path': AUDIO_PATH,
    'style': 'cinematic',
    'duration_seconds': 2,
    'script_id': script_id,
}
scene_resp = requests.post(f'{BASE_URL}/scenes', json=scene_payload)
print('Scene status:', scene_resp.status_code, scene_resp.text)
scene_id = scene_resp.json()['id']

print('Calling generate-video...')
gen_resp = requests.post(f'{BASE_URL}/scenes/{scene_id}/generate-video')
print('Generate-video status:', gen_resp.status_code)
try:
    print(gen_resp.json())
except ValueError:
    print(gen_resp.text)

print('Scene details:', requests.get(f'{BASE_URL}/scenes/{scene_id}').json())
