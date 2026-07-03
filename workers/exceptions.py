"""Custom exceptions for video generation workers."""


class VideoGenerationError(Exception):
    """Base exception for video generation errors."""
    pass


class ModelServerError(VideoGenerationError):
    """Raised when the AnimateDiff model server fails."""
    pass


class FFmpegError(VideoGenerationError):
    """Raised when FFmpeg operations fail."""
    pass


class FileIOError(VideoGenerationError):
    """Raised when file I/O operations fail."""
    pass


class ValidationError(VideoGenerationError):
    """Raised when input validation fails."""
    pass


class TimeoutError(VideoGenerationError):
    """Raised when an operation times out."""
    pass
