import base64
import requests
import os
import shutil
import tempfile
import logging
import subprocess
import numpy as np
from typing import Optional
from tenacity import retry, stop_after_attempt, wait_exponential

from workers.exceptions import (
    ModelServerError, FFmpegError, FileIOError, ValidationError, TimeoutError
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Configuration from environment variables
ANIMATEDIFF_URL = os.environ.get("ANIMATEDIFF_URL", "http://localhost:8001/generate")
ANIMATEDIFF_TIMEOUT = int(os.environ.get("ANIMATEDIFF_TIMEOUT", "300"))
TEMP_DIR = os.environ.get("TEMP_DIR", tempfile.gettempdir())
FFMPEG_TIMEOUT = int(os.environ.get("FFMPEG_TIMEOUT", "600"))
MAX_VIDEO_DURATION = int(os.environ.get("MAX_VIDEO_DURATION", "300"))
ALLOW_PLACEHOLDER_VIDEO = os.environ.get("ALLOW_PLACEHOLDER_VIDEO", "true").lower() in ("1", "true", "yes")
PLACEHOLDER_VIDEO_CODEC = os.environ.get("PLACEHOLDER_VIDEO_CODEC", "mp4v")
PLACEHOLDER_VIDEO_FPS = int(os.environ.get("PLACEHOLDER_VIDEO_FPS", "12"))

SUPPORTED_STYLES = {
    "cinematic": "cinematic lighting, dramatic, film look",
    "faceless_broll": "b-roll, faceless, aesthetic, smooth motion",
    "animated": "stylized, anime, vibrant colors",
    "avatar": "talking head, expressive face, studio lighting"
}


def validate_inputs(image_path: str, audio_path: str, style: str, duration: int) -> None:
    """
    Validate all input parameters before processing.
    
    Raises ValidationError if any input is invalid.
    """
    logger.info(f"Validating inputs: image={image_path}, audio={audio_path}, style={style}, duration={duration}")
    
    # Check image exists
    if not os.path.exists(image_path):
        raise ValidationError(f"Image file not found: {image_path}")
    
    # Check audio exists
    if not os.path.exists(audio_path):
        raise ValidationError(f"Audio file not found: {audio_path}")
    
    # Check style is supported
    if style not in SUPPORTED_STYLES:
        raise ValidationError(f"Unsupported style '{style}'. Supported: {list(SUPPORTED_STYLES.keys())}")
    
    # Check duration is valid
    if duration <= 0 or duration > MAX_VIDEO_DURATION:
        raise ValidationError(f"Duration must be between 1 and {MAX_VIDEO_DURATION} seconds")
    
    logger.info("Input validation passed")


def ffmpeg_available() -> bool:
    """Return True when a local ffmpeg executable is available."""
    return shutil.which("ffmpeg") is not None


def create_placeholder_video(image_path: str, duration: int, output_path: str, fps: int = PLACEHOLDER_VIDEO_FPS) -> None:
    """Create a placeholder MP4 from a still image for local testing."""
    logger.info(f"Creating placeholder video: image={image_path}, duration={duration}, fps={fps}")

    try:
        from PIL import Image
        import imageio.v3 as iio
    except ImportError as e:
        raise FileIOError(
            "Pillow and imageio are required for placeholder fallback video generation. "
            "Install Pillow and imageio."
        ) from e

    try:
        image = Image.open(image_path).convert("RGB")
    except Exception as e:
        raise FileIOError(f"Failed to read image for placeholder video: {e}") from e

    frame = np.array(image)
    frame_count = int(duration * fps)

    try:
        iio.imwrite(
            output_path,
            [frame] * frame_count,
            fps=fps,
        )
    except Exception as e:
        raise FFmpegError(f"Failed to write placeholder video: {e}") from e

    logger.info(f"Placeholder video created at {output_path}")


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
    reraise=True
)
def call_animatediff_server(image_b64: str, prompt: str, num_frames: int, fps: int) -> str:
    """
    Call the AnimateDiff model server with retry logic.
    
    Args:
        image_b64: Base64-encoded image
        prompt: Text prompt for video generation
        num_frames: Number of frames to generate
        fps: Frames per second
    
    Returns:
        Base64-encoded video
    
    Raises:
        ModelServerError if the server call fails
    """
    logger.info(f"Calling AnimateDiff server with prompt: {prompt}")
    
    try:
        resp = requests.post(
            ANIMATEDIFF_URL,
            json={
                "prompt": prompt,
                "image_base64": image_b64,
                "num_frames": num_frames,
                "fps": fps
            },
            timeout=ANIMATEDIFF_TIMEOUT
        )
        resp.raise_for_status()
        response = resp.json()
        
        if "video_base64" not in response:
            raise ModelServerError("No video returned from AnimateDiff server")
        
        logger.info("AnimateDiff server call successful")
        return response["video_base64"]
    
    except requests.exceptions.Timeout:
        logger.error(f"AnimateDiff server timeout after {ANIMATEDIFF_TIMEOUT}s")
        raise ModelServerError(f"AnimateDiff server timeout after {ANIMATEDIFF_TIMEOUT}s")
    except requests.exceptions.ConnectionError as e:
        logger.error(f"Failed to connect to AnimateDiff server: {e}")
        raise ModelServerError(f"Failed to connect to AnimateDiff server at {ANIMATEDIFF_URL}: {e}")
    except requests.exceptions.RequestException as e:
        logger.error(f"AnimateDiff server error: {e}")
        raise ModelServerError(f"AnimateDiff server error: {e}")


def generate_video_with_model(
    image_path: str,
    audio_path: str,
    style: str,
    duration: int,
    output_path: str
) -> str:
    """
    Generate a video by combining an image and audio using AnimateDiff.
    
    Args:
        image_path: Path to input image
        audio_path: Path to input audio
        style: Video style (cinematic, faceless_broll, animated, avatar)
        duration: Video duration in seconds
        output_path: Path to output video file
    
    Returns:
        Path to generated video
    
    Raises:
        ValidationError: If inputs are invalid
        ModelServerError: If AnimateDiff call fails
        FFmpegError: If audio merging fails
        FileIOError: If file operations fail
    """
    temp_video_path = None
    
    try:
        # Validate all inputs
        validate_inputs(image_path, audio_path, style, duration)
        
        # Read image as base64
        logger.info(f"Reading image from {image_path}")
        try:
            with open(image_path, "rb") as f:
                img_b64 = base64.b64encode(f.read()).decode()
        except IOError as e:
            raise FileIOError(f"Failed to read image file: {e}")
        
        # Get prompt for style
        prompt = SUPPORTED_STYLES.get(style, "cinematic")
        logger.info(f"Using prompt: {prompt}")
        
        # Call AnimateDiff server
        num_frames = int(duration * PLACEHOLDER_VIDEO_FPS)
        try:
            video_b64 = call_animatediff_server(img_b64, prompt, num_frames, fps=PLACEHOLDER_VIDEO_FPS)
            # Save video to temp file
            logger.info("Decoding and saving video to temp file")
            try:
                with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=TEMP_DIR) as tmp_vid:
                    temp_video_path = tmp_vid.name
                    tmp_vid.write(base64.b64decode(video_b64))
                logger.info(f"Saved temp video to {temp_video_path}")
            except IOError as e:
                raise FileIOError(f"Failed to write temp video file: {e}")

        except ModelServerError as exc:
            if not ALLOW_PLACEHOLDER_VIDEO:
                raise

            logger.warning(
                "AnimateDiff server unavailable, falling back to local placeholder video: %s",
                exc,
            )
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4", dir=TEMP_DIR) as tmp_vid:
                temp_video_path = tmp_vid.name
            create_placeholder_video(image_path, duration, temp_video_path, fps=PLACEHOLDER_VIDEO_FPS)

        # Merge audio with FFmpeg when available; otherwise keep the generated video only.
        try:
            if ffmpeg_available():
                logger.info(f"Merging audio from {audio_path} into video")
                merge_audio(temp_video_path, audio_path, output_path)
            else:
                logger.warning("FFmpeg is not installed or not available on PATH; creating video without audio")
                shutil.copyfile(temp_video_path, output_path)
        except FFmpegError as exc:
            if ALLOW_PLACEHOLDER_VIDEO:
                logger.warning(
                    "Audio merge failed; writing video without audio and continuing: %s",
                    exc,
                )
                shutil.copyfile(temp_video_path, output_path)
            else:
                raise

        logger.info(f"Video generation complete: {output_path}")
        return output_path

    except Exception as e:
        logger.error(f"Error in generate_video_with_model: {type(e).__name__}: {e}")
        raise
    finally:
        # Clean up temp video file
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.remove(temp_video_path)
                logger.info(f"Cleaned up temp video file: {temp_video_path}")
            except OSError as e:
                logger.warning(f"Failed to clean up temp file {temp_video_path}: {e}")


def merge_audio(video_path: str, audio_path: str, output_path: str) -> None:
    """
    Merge audio with video using FFmpeg.
    
    Args:
        video_path: Path to video file
        audio_path: Path to audio file
        output_path: Path to output file
    
    Raises:
        FFmpegError: If FFmpeg command fails
    """
    cmd = [
        "ffmpeg",
        "-i", video_path,
        "-i", audio_path,
        "-c:v", "copy",
        "-c:a", "aac",
        "-shortest",
        output_path,
        "-y"
    ]
    
    try:
        logger.info(f"Running FFmpeg: {' '.join(cmd)}")
        subprocess.run(cmd, check=True, timeout=FFMPEG_TIMEOUT, capture_output=True)
        logger.info(f"Audio merge successful: {output_path}")
    except subprocess.TimeoutExpired:
        logger.error(f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")
        raise FFmpegError(f"FFmpeg timed out after {FFMPEG_TIMEOUT}s")
    except subprocess.CalledProcessError as e:
        logger.error(f"FFmpeg error: {e.stderr.decode() if e.stderr else str(e)}")
        raise FFmpegError(f"FFmpeg failed: {e}")
    except Exception as e:
        logger.error(f"Error running FFmpeg: {e}")
        raise FFmpegError(f"Error running FFmpeg: {e}")
