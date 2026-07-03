"""Async video generation for concurrent processing."""

import asyncio
import httpx
import base64
import os
import tempfile
import logging
from typing import Optional

from workers.exceptions import ModelServerError, FFmpegError, ValidationError

logger = logging.getLogger(__name__)

# Configuration
ANIMATEDIFF_URL = os.environ.get("ANIMATEDIFF_URL", "http://localhost:8001/generate")
ANIMATEDIFF_TIMEOUT = int(os.environ.get("ANIMATEDIFF_TIMEOUT", "300"))
TEMP_DIR = os.environ.get("TEMP_DIR", "/tmp")


async def call_animatediff_server_async(
    image_b64: str,
    prompt: str,
    num_frames: int,
    fps: int
) -> str:
    """
    Async call to AnimateDiff model server.
    
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
    async with httpx.AsyncClient(timeout=ANIMATEDIFF_TIMEOUT) as client:
        try:
            resp = await client.post(
                ANIMATEDIFF_URL,
                json={
                    "prompt": prompt,
                    "image_base64": image_b64,
                    "num_frames": num_frames,
                    "fps": fps
                }
            )
            resp.raise_for_status()
            response = resp.json()
            
            if "video_base64" not in response:
                raise ModelServerError("No video returned from AnimateDiff server")
            
            logger.info("Async AnimateDiff server call successful")
            return response["video_base64"]
        
        except httpx.TimeoutException:
            logger.error(f"AnimateDiff server timeout after {ANIMATEDIFF_TIMEOUT}s")
            raise ModelServerError(f"AnimateDiff server timeout after {ANIMATEDIFF_TIMEOUT}s")
        except httpx.ConnectError as e:
            logger.error(f"Failed to connect to AnimateDiff server: {e}")
            raise ModelServerError(f"Failed to connect to AnimateDiff server: {e}")
        except Exception as e:
            logger.error(f"AnimateDiff server error: {e}")
            raise ModelServerError(f"AnimateDiff server error: {e}")


async def generate_video_batch_async(
    jobs: list[dict]
) -> list[str]:
    """
    Generate multiple videos concurrently.
    
    Args:
        jobs: List of job dictionaries with keys:
            - image_path: Path to image
            - audio_path: Path to audio
            - style: Video style
            - duration: Duration in seconds
            - output_path: Output path
    
    Returns:
        List of output paths for successful jobs
    
    Raises:
        Exception if any job fails
    """
    logger.info(f"Starting batch generation for {len(jobs)} videos")
    
    tasks = []
    for job in jobs:
        # Import here to avoid circular imports
        from workers.video_generator import generate_video_with_model
        
        task = asyncio.to_thread(
            generate_video_with_model,
            job["image_path"],
            job["audio_path"],
            job["style"],
            job["duration"],
            job["output_path"]
        )
        tasks.append(task)
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Check for failures
    output_paths = []
    for i, result in enumerate(results):
        if isinstance(result, Exception):
            logger.error(f"Job {i} failed: {result}")
            raise result
        else:
            output_paths.append(result)
    
    logger.info(f"Batch generation complete: {len(output_paths)} videos")
    return output_paths


def run_batch_generation(jobs: list[dict]) -> list[str]:
    """
    Run batch video generation (blocking wrapper for async function).
    
    Args:
        jobs: List of job dictionaries
    
    Returns:
        List of output paths
    """
    return asyncio.run(generate_video_batch_async(jobs))
