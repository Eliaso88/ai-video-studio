import json
import urllib.request

import urllib.request, urllib.error

scripts_url = 'http://127.0.0.1:8000/api/scripts'
try:
    with urllib.request.urlopen(scripts_url) as r:
        scripts_list = json.loads(r.read().decode('utf-8'))
except Exception as e:
    print('Failed to fetch scripts list:', e)
    raise

if not scripts_list:
    raise SystemExit('No scripts available to test. Run the E2E helper to create one.')

script_id = scripts_list[0]['id']
url = f'http://127.0.0.1:8000/api/render/{script_id}'

payload = {
    "aspect_ratio": "9:16",
    "resolution": "1080p",
    "music_style": "cinematic",
    "niche": "AI choose best niche",
    "language_voice": "AI choose best voice",
    "background_music": "AI choose music",
    "art_style": "AI choose style",
    "caption_style": "AI choose caption style",
    "effects": "AI choose effect",
    "social_accounts": "@test",
    "duration_seconds": 60,
}
req = urllib.request.Request(url, data=json.dumps(payload).encode('utf-8'), headers={"Content-Type": "application/json"})
with urllib.request.urlopen(req) as r:
    print('status', r.status)
    body = r.read().decode('utf-8')
    print(body)
