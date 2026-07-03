"""Unit tests for video generation workers."""

import pytest
import os
import tempfile
from unittest.mock import patch, MagicMock, mock_open
import base64

from workers.video_generator import (
    validate_inputs,
    call_animatediff_server,
    generate_video_with_model,
    merge_audio
)
from workers.exceptions import (
    ValidationError, ModelServerError, FFmpegError, FileIOError
)


class TestValidateInputs:
    """Tests for input validation."""
    
    def test_valid_inputs(self, tmp_path):
        """Test validation passes with valid inputs."""
        image_file = tmp_path / "image.png"
        image_file.write_text("fake image")
        
        audio_file = tmp_path / "audio.mp3"
        audio_file.write_text("fake audio")
        
        # Should not raise
        validate_inputs(str(image_file), str(audio_file), "cinematic", 10)
    
    def test_missing_image(self):
        """Test validation fails if image doesn't exist."""
        with pytest.raises(ValidationError, match="Image file not found"):
            validate_inputs("/nonexistent/image.png", "/nonexistent/audio.mp3", "cinematic", 10)
    
    def test_missing_audio(self, tmp_path):
        """Test validation fails if audio doesn't exist."""
        image_file = tmp_path / "image.png"
        image_file.write_text("fake image")
        
        with pytest.raises(ValidationError, match="Audio file not found"):
            validate_inputs(str(image_file), "/nonexistent/audio.mp3", "cinematic", 10)
    
    def test_invalid_style(self, tmp_path):
        """Test validation fails for unsupported style."""
        image_file = tmp_path / "image.png"
        image_file.write_text("fake image")
        
        audio_file = tmp_path / "audio.mp3"
        audio_file.write_text("fake audio")
        
        with pytest.raises(ValidationError, match="Unsupported style"):
            validate_inputs(str(image_file), str(audio_file), "invalid_style", 10)
    
    def test_invalid_duration(self, tmp_path):
        """Test validation fails for invalid duration."""
        image_file = tmp_path / "image.png"
        image_file.write_text("fake image")
        
        audio_file = tmp_path / "audio.mp3"
        audio_file.write_text("fake audio")
        
        with pytest.raises(ValidationError, match="Duration must be"):
            validate_inputs(str(image_file), str(audio_file), "cinematic", 0)
        
        with pytest.raises(ValidationError, match="Duration must be"):
            validate_inputs(str(image_file), str(audio_file), "cinematic", 400)


class TestCallAnimatediffServer:
    """Tests for AnimateDiff server calls."""
    
    @patch('workers.video_generator.requests.post')
    def test_successful_call(self, mock_post):
        """Test successful AnimateDiff server call."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"video_base64": "base64_video_data"}
        mock_post.return_value = mock_response
        
        result = call_animatediff_server("base64_image", "test prompt", 16, 12)
        assert result == "base64_video_data"
    
    @patch('workers.video_generator.requests.post')
    def test_missing_video_in_response(self, mock_post):
        """Test error when video_base64 not in response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {"error": "some error"}
        mock_post.return_value = mock_response
        
        with pytest.raises(ModelServerError, match="No video returned"):
            call_animatediff_server("base64_image", "test prompt", 16, 12)
    
    @patch('workers.video_generator.requests.post')
    def test_connection_error(self, mock_post):
        """Test error on connection failure."""
        import requests
        mock_post.side_effect = requests.exceptions.ConnectionError("Connection failed")
        
        with pytest.raises(ModelServerError, match="Failed to connect"):
            call_animatediff_server("base64_image", "test prompt", 16, 12)
    
    @patch('workers.video_generator.requests.post')
    def test_timeout_error(self, mock_post):
        """Test error on timeout."""
        import requests
        mock_post.side_effect = requests.exceptions.Timeout("Request timeout")
        
        with pytest.raises(ModelServerError, match="timeout"):
            call_animatediff_server("base64_image", "test prompt", 16, 12)


class TestMergeAudio:
    """Tests for audio merging."""
    
    @patch('workers.video_generator.subprocess.run')
    def test_successful_merge(self, mock_run, tmp_path):
        """Test successful audio merge."""
        video_file = tmp_path / "video.mp4"
        video_file.write_text("fake video")
        
        audio_file = tmp_path / "audio.mp3"
        audio_file.write_text("fake audio")
        
        output_file = tmp_path / "output.mp4"
        
        # Should not raise
        merge_audio(str(video_file), str(audio_file), str(output_file))
        mock_run.assert_called_once()
    
    @patch('workers.video_generator.subprocess.run')
    def test_ffmpeg_failure(self, mock_run, tmp_path):
        """Test error on FFmpeg failure."""
        import subprocess
        mock_run.side_effect = subprocess.CalledProcessError(1, "ffmpeg")
        
        with pytest.raises(FFmpegError):
            merge_audio("/fake/video.mp4", "/fake/audio.mp3", "/fake/output.mp4")
    
    @patch('workers.video_generator.subprocess.run')
    def test_ffmpeg_timeout(self, mock_run):
        """Test error on FFmpeg timeout."""
        import subprocess
        mock_run.side_effect = subprocess.TimeoutExpired("ffmpeg", 300)
        
        with pytest.raises(FFmpegError, match="timed out"):
            merge_audio("/fake/video.mp4", "/fake/audio.mp3", "/fake/output.mp4")


class TestGenerateVideoWithModel:
    """Tests for the main video generation function."""
    
    @patch('workers.video_generator.merge_audio')
    @patch('workers.video_generator.call_animatediff_server')
    def test_successful_generation(self, mock_animatediff, mock_merge, tmp_path):
        """Test successful video generation."""
        image_file = tmp_path / "image.png"
        image_file.write_bytes(b"fake image")
        
        audio_file = tmp_path / "audio.mp3"
        audio_file.write_bytes(b"fake audio")
        
        output_file = tmp_path / "output.mp4"
        
        # Mock AnimateDiff response
        fake_video = b"fake_video_content"
        mock_animatediff.return_value = base64.b64encode(fake_video).decode()
        
        result = generate_video_with_model(
            str(image_file),
            str(audio_file),
            "cinematic",
            10,
            str(output_file)
        )
        
        assert result == str(output_file)
        mock_animatediff.assert_called_once()
        mock_merge.assert_called_once()
    
    def test_validation_error(self, tmp_path):
        """Test error on invalid inputs."""
        with pytest.raises(ValidationError):
            generate_video_with_model(
                "/nonexistent/image.png",
                "/nonexistent/audio.mp3",
                "cinematic",
                10,
                str(tmp_path / "output.mp4")
            )
