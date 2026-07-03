import os
import requests
import uuid

base = 'http://127.0.0.1:8000/api'
# Use known example URLs instead of fetching an existing scene
img_url = 'https://via.placeholder.com/640x360.png'
aud_url = 'https://interactive-examples.mdn.mozilla.net/media/examples/t-rex-roar.mp3'
print('Downloading', img_url, 'and', aud_url)
up_dir = os.path.join(os.path.dirname(__file__), '..', 'static', 'uploads')
os.makedirs(up_dir, exist_ok=True)
uid = str(uuid.uuid4())
img_path = os.path.abspath(os.path.join(up_dir, f"scene_{uid}_image.jpg"))
aud_path = os.path.abspath(os.path.join(up_dir, f"scene_{uid}_audio.mp3"))

with requests.get(img_url, stream=True) as r:
    r.raise_for_status()
    with open(img_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)
with requests.get(aud_url, stream=True) as r:
    r.raise_for_status()
    with open(aud_path, 'wb') as f:
        for chunk in r.iter_content(chunk_size=8192):
            f.write(chunk)

print('Saved to', img_path, aud_path)
scene_payload = {
    'title': 'Local Video Scene',
    'description': 'Downloaded assets',
    'image_path': img_path,
    'audio_path': aud_path,
    'style': 'cinematic',
    'duration_seconds': 6,
        'script_id': '1931eced-db7e-4d02-9e33-8749e862db7e'
}

r = requests.post(f'{base}/scenes', json=scene_payload)
print('CREATE SCENE', r.status_code, r.json())
new_sid = r.json()['id']

print('Calling generate-video for', new_sid)
rv = requests.post(f'{base}/scenes/{new_sid}/generate-video')
print('GENERATE-VIDEO', rv.status_code)
try:
    print(rv.json())
except Exception:
    print(rv.text)

f = requests.get(f'{base}/scenes/{new_sid}')
print('FINAL SCENE', f.status_code, f.json())
