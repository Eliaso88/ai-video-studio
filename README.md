# AI Video Generation

This repository contains a backend + worker pipeline for generating AI video from script scenes, voice audio, and AnimateDiff model integration.

## What’s included

- `workers/video_generator.py` — enhanced worker implementation with validation, logging, retries, and FFmpeg merging
- `workers/video_generator_async.py` — async batch generation support
- `workers/exceptions.py` — custom error classes for clear failure handling
- `workers/test_video_generator.py` — unit tests for the worker logic
- `workers/requirements_test.txt` — lightweight dependencies for running tests
- `.github/workflows/python-tests.yml` — GitHub Actions workflow for CI

## Quickstart

### 1. Install Python

Ensure Python is installed and available on your PATH:

```powershell
python --version
```

### 2. Create a virtual environment

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

### 3. Install test dependencies

```powershell
python -m pip install --upgrade pip
python -m pip install -r workers/requirements_test.txt
```

### 4. Run the unit tests

```powershell
pytest workers/test_video_generator.py -v
```

## GitHub Actions CI

The repository includes a CI workflow at `.github/workflows/python-tests.yml` that runs tests on `push` and `pull_request` for Python `3.12` and `3.14`.

## Notes

- The worker uses environment variables for configuration (see `.env.example`).
- If the AnimateDiff server is unavailable, the backend can fall back to a local placeholder video when `ALLOW_PLACEHOLDER_VIDEO=true`.
- Set `ANIMATEDIFF_URL` to match your model server endpoint if it is not running on `http://localhost:8001/generate`.
- If you want full runtime support, install the dependencies in `requirements.txt`.
- The test suite currently verifies the core worker functions and validation logic.

## Backend API

A minimal FastAPI backend is available under `backend/`.

### Run the backend

```powershell
python -m pip install --upgrade pip
python -m pip install -r requirements-backend.txt
python -m uvicorn backend.app:app --reload --host 0.0.0.0 --port 8000
```

### Sample endpoints

- `GET /api/health`
- `POST /api/scenes` - create a scene
- `GET /api/scenes/{scene_id}` - retrieve scene metadata
- `POST /api/scenes/{scene_id}/generate-video` - generate a video for a scene
- `GET /api/assets/videos/{filename}` - serve generated video files

## Frontend

The frontend is in `frontend/` and uses Next.js.

```powershell
cd frontend
npm install
npm run dev
```

Then open `http://localhost:3000` in your browser.

## E2E and Automation

Quick steps to run the end-to-end flow (creates a script/scene, generates a placeholder video, and opens the render page):

1. Start the backend API:

```powershell
python -m uvicorn backend.app:app --reload --host 127.0.0.1 --port 8000
```

2. Start the frontend dev server:

```powershell
cd frontend
npm install
npm run dev
```

3. Create test assets (this helper creates an image, audio, script, scene, and generates a placeholder video):

```powershell
python backend/scripts/e2e_test.py
```

4. Open the render URL printed by the E2E helper, e.g. `http://127.0.0.1:3000/render/<script_id>` and confirm playback.

5. Optional — run Playwright E2E test (requires Playwright install):

```powershell
cd frontend
npm install
npx playwright install
npm run test:e2e
```

Notes:
- Automation settings are persisted per-script when saved in the Script editor (`Save Automation Settings`).
- The backend applies simple heuristics to resolve `AI choose...` placeholders; you can replace this logic with an external AI service if desired.
