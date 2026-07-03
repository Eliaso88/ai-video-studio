import requests
base='http://127.0.0.1:8000/api'
r=requests.post(base+'/scripts',json={'title':'Sample Script','description':'Recreated'})
print('SCRIPT', r.status_code, r.json())
sid=r.json()['id']
s=requests.post(base+'/scenes',json={'title':'Intro Scene','description':'Assistant-created scene','image_path':'https://via.placeholder.com/640x360.png','audio_path':'https://interactive-examples.mdn.mozilla.net/media/examples/t-rex-roar.mp3','style':'cinematic','duration_seconds':6,'script_id':sid})
print('SCENE', s.status_code, s.json())
attach=requests.post(base+f'/admin/scenes/{s.json()["id"]}/attach-placeholder-video')
print('ATTACH', attach.status_code, attach.json())
print('FRONTEND_URL: http://localhost:3000/render/'+sid)
