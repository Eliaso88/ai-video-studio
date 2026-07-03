import argparse
import logging

from workers.video_generator import generate_video_with_model
from workers.exceptions import VideoGenerationError

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run video generation from image and audio.")
    parser.add_argument("--image", required=True, help="Path to the input image file")
    parser.add_argument("--audio", required=True, help="Path to the input audio file")
    parser.add_argument("--style", default="cinematic", choices=["cinematic", "faceless_broll", "animated", "avatar"], help="Video generation style")
    parser.add_argument("--duration", type=int, default=10, help="Duration in seconds")
    parser.add_argument("--output", default="output_video.mp4", help="Path for the generated output video")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    logger.info("Starting video generation")
    logger.info(f"Image: {args.image}")
    logger.info(f"Audio: {args.audio}")
    logger.info(f"Style: {args.style}")
    logger.info(f"Duration: {args.duration}s")
    logger.info(f"Output: {args.output}")

    try:
        output_path = generate_video_with_model(
            image_path=args.image,
            audio_path=args.audio,
            style=args.style,
            duration=args.duration,
            output_path=args.output,
        )
        logger.info(f"Video generated successfully: {output_path}")
        return 0
    except VideoGenerationError as exc:
        logger.error(f"Video generation failed: {exc}")
        return 1
    except Exception as exc:
        logger.exception("Unexpected error during video generation")
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
