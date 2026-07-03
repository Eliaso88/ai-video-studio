# AI Video Generation - Enhanced Video Worker

This module provides production-ready video generation with all 7 enhancements implemented.

## Enhancements Overview

### 1. Detailed Logging ✅
- Uses Python's `logging` module for structured logging
- Configurable log levels via environment variables
- Tracks all major operations and errors with timestamps

### 2. Custom Exceptions & User Feedback ✅
- **VideoGenerationError**: Base exception class
- **ModelServerError**: AnimateDiff/model failures
- **FFmpegError**: FFmpeg operation failures
- **FileIOError**: File system issues
- **ValidationError**: Input validation failures
- **TimeoutError**: Operation timeouts

See `workers/exceptions.py` for details.

### 3. Configurable Parameters ✅
All parameters configurable via environment variables:
- `ANIMATEDIFF_URL`: Model server endpoint (default: http://localhost:8001/generate)
- `ANIMATEDIFF_TIMEOUT`: Request timeout in seconds (default: 300)
- `TEMP_DIR`: Temporary file directory (default: /tmp)
- `FFMPEG_TIMEOUT`: FFmpeg operation timeout (default: 600)
- `MAX_VIDEO_DURATION`: Maximum allowed duration (default: 300 seconds)
- `LOG_LEVEL`: Logging level (default: INFO)

Copy `.env.example` to `.env` and customize:
```bash
cp .env.example .env
# Edit .env with your values
```

### 4. Timeouts & Retries ✅
- **Automatic retry logic** using `tenacity` library
  - Retries up to 3 times with exponential backoff
  - Wait 2-10 seconds between retries
- **Configurable timeouts** for all operations
- **Graceful error handling** for network and service failures

Example retry behavior:
```
Attempt 1: Fails → Wait 2 seconds
Attempt 2: Fails → Wait 4 seconds  
Attempt 3: Fails → Raise exception
```

### 5. Input Validation ✅
Comprehensive validation in `validate_inputs()`:
- ✓ Image file existence
- ✓ Audio file existence
- ✓ Supported style (cinematic, faceless_broll, animated, avatar)
- ✓ Duration range (1 to MAX_VIDEO_DURATION seconds)

All validations run before processing to fail fast.

### 6. Unit Tests ✅
Complete test suite in `test_video_generator.py`:
- **TestValidateInputs**: Input validation tests
- **TestCallAnimatediffServer**: Model server call tests
- **TestMergeAudio**: FFmpeg audio merge tests
- **TestGenerateVideoWithModel**: End-to-end generation tests

Run tests:
```bash
pytest workers/test_video_generator.py -v
pytest workers/test_video_generator.py --cov=workers.video_generator
```

### 7. Parallel/Async Processing ✅
Async implementation in `video_generator_async.py`:
- Uses `httpx` for async HTTP requests
- `generate_video_batch_async()` for concurrent video generation
- `asyncio.to_thread()` for CPU-bound operations (FFmpeg)

Example batch processing:
```python
from workers.video_generator_async import run_batch_generation

jobs = [
    {
        "image_path": "scene1_image.png",
        "audio_path": "scene1_audio.mp3",
        "style": "cinematic",
        "duration": 10,
        "output_path": "scene1_video.mp4"
    },
    # ... more jobs
]

output_paths = run_batch_generation(jobs)
```

## Usage

### Basic Usage (Single Video)

```python
from workers.video_generator import generate_video_with_model

output = generate_video_with_model(
    image_path="input_image.png",
    audio_path="input_audio.mp3",
    style="cinematic",
    duration=10,
    output_path="output_video.mp4"
)
print(f"Generated: {output}")
```

### Batch Processing (Multiple Videos)

```python
from workers.video_generator_async import run_batch_generation

jobs = [
    # ... job definitions
]

results = run_batch_generation(jobs)
for output_path in results:
    print(f"Generated: {output_path}")
```

### With Error Handling

```python
from workers.video_generator import generate_video_with_model
from workers.exceptions import ValidationError, ModelServerError, FFmpegError

try:
    output = generate_video_with_model(
        image_path="image.png",
        audio_path="audio.mp3",
        style="cinematic",
        duration=10,
        output_path="output.mp4"
    )
except ValidationError as e:
    print(f"Input validation failed: {e}")
except ModelServerError as e:
    print(f"Model server error: {e}")
except FFmpegError as e:
    print(f"FFmpeg error: {e}")
```

## Installation

1. Install dependencies:
```bash
pip install -r requirements.txt
```

2. Install FFmpeg (if not already installed):
```bash
# Ubuntu/Debian
sudo apt-get install ffmpeg

# macOS
brew install ffmpeg

# Windows
choco install ffmpeg
```

3. Set up environment:
```bash
cp .env.example .env
# Edit .env with your configuration
```

4. Start AnimateDiff model server (on separate machine/GPU):
```bash
python -m uvicorn animatediff_server:app --host 0.0.0.0 --port 8001
```

5. Run tests:
```bash
pytest workers/test_video_generator.py -v
```

## Logging Output Example

```
INFO:workers.video_generator:Validating inputs: image=image.png, audio=audio.mp3, style=cinematic, duration=10
INFO:workers.video_generator:Input validation passed
INFO:workers.video_generator:Reading image from image.png
INFO:workers.video_generator:Using prompt: cinematic lighting, dramatic, film look
INFO:workers.video_generator:Calling AnimateDiff server with prompt: cinematic lighting, dramatic, film look
INFO:workers.video_generator:AnimateDiff server call successful
INFO:workers.video_generator:Decoding and saving video to temp file
INFO:workers.video_generator:Saved temp video to /tmp/tmpxyz.mp4
INFO:workers.video_generator:Merging audio from audio.mp3 into video
INFO:workers.video_generator:Running FFmpeg: ffmpeg -i /tmp/tmpxyz.mp4 -i audio.mp3 ...
INFO:workers.video_generator:Audio merge successful: output.mp4
INFO:workers.video_generator:Video generation complete: output.mp4
INFO:workers.video_generator:Cleaned up temp video file: /tmp/tmpxyz.mp4
```

## Performance Considerations

- **Memory**: AnimateDiff requires significant GPU memory (recommend 8GB+)
- **Time**: Typical video generation takes 2-5 minutes depending on duration
- **Batch Processing**: Can generate multiple videos concurrently on same GPU with memory management
- **Retry Logic**: Exponential backoff prevents overwhelming failing services

## Troubleshooting

### Model Server Timeout
- Increase `ANIMATEDIFF_TIMEOUT` for slower GPUs
- Check model server is running: `curl http://localhost:8001/health`

### FFmpeg Errors
- Ensure FFmpeg is installed: `ffmpeg -version`
- Increase `FFMPEG_TIMEOUT` for longer videos
- Check audio format compatibility

### Validation Errors
- Verify image format is PNG/JPG
- Verify audio format is MP3/WAV
- Check style is one of: cinematic, faceless_broll, animated, avatar

## Architecture

```
video_generator.py (main sync module)
├── validate_inputs() - Input validation
├── call_animatediff_server() - Model call with retries
├── merge_audio() - FFmpeg audio merge
└── generate_video_with_model() - Orchestrator

video_generator_async.py (async module)
├── call_animatediff_server_async() - Async model call
├── generate_video_batch_async() - Concurrent batch processing
└── run_batch_generation() - Blocking wrapper

exceptions.py (custom exceptions)
├── ValidationError
├── ModelServerError
├── FFmpegError
└── FileIOError

test_video_generator.py (comprehensive tests)
├── TestValidateInputs
├── TestCallAnimatediffServer
├── TestMergeAudio
└── TestGenerateVideoWithModel
```

## Next Steps

1. Deploy AnimateDiff model server to GPU infrastructure
2. Configure Redis and RQ for distributed job processing
3. Set up S3 for video storage
4. Integrate with your FastAPI backend at `/scenes/{scene_id}/generate-video`
5. Monitor logs and adjust timeouts based on performance

## Support

For issues or questions, check:
- Logs in `LOG_LEVEL` output
- Test results in `test_video_generator.py`
- Environment configuration in `.env`
