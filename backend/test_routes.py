from fastapi.testclient import TestClient

from backend.app import app

client = TestClient(app)


def test_script_lifecycle() -> None:
    response = client.post("/api/scripts", json={"title": "Test Script", "description": "A test script."})
    assert response.status_code == 200
    script = response.json()
    assert script["id"]
    assert script["title"] == "Test Script"

    script_id = script["id"]

    list_response = client.get("/api/scripts")
    assert list_response.status_code == 200
    scripts = list_response.json()
    assert any(item["id"] == script_id for item in scripts)

    get_response = client.get(f"/api/scripts/{script_id}")
    assert get_response.status_code == 200
    payload = get_response.json()
    assert payload["script"]["id"] == script_id
    assert payload["script"]["title"] == "Test Script"
    assert payload["scenes"] == []


def test_scene_patch_and_generate_endpoints() -> None:
    script_resp = client.post("/api/scripts", json={"title": "Patch Script", "description": "Another test."})
    assert script_resp.status_code == 200
    script_id = script_resp.json()["id"]

    create_scene = client.post(
        "/api/scenes",
        json={
            "script_id": script_id,
            "title": "Scene One",
            "description": "Test scene description.",
            "image_path": "https://example.com/image.png",
            "audio_path": "https://example.com/audio.mp3",
            "style": "cinematic",
            "duration_seconds": 5,
        },
    )
    assert create_scene.status_code == 200
    scene = create_scene.json()
    scene_id = scene["id"]
    assert scene["script_id"] == script_id

    patch_response = client.patch(
        f"/api/scenes/{scene_id}", json={"title": "Scene One Updated", "duration_seconds": 8}
    )
    assert patch_response.status_code == 200
    updated_scene = patch_response.json()
    assert updated_scene["title"] == "Scene One Updated"
    assert updated_scene["duration_seconds"] == 8

    image_response = client.post(f"/api/scenes/{scene_id}/generate-image")
    assert image_response.status_code == 200
    assert image_response.json().get("image_url")

    voice_response = client.post(f"/api/scenes/{scene_id}/generate-voice")
    assert voice_response.status_code == 200
    assert voice_response.json().get("voice_audio_url")

    get_script_response = client.get(f"/api/scripts/{script_id}")
    assert get_script_response.status_code == 200
    payload = get_script_response.json()
    assert len(payload["scenes"]) == 1
    assert payload["scenes"][0]["id"] == scene_id
    assert payload["scenes"][0]["image_url"]
    assert payload["scenes"][0]["voice_audio_url"]
