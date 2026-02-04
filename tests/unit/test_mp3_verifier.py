"""Unit tests for MP3Verifier."""

import pytest

from audio_generation.verification.mp3_verifier import MP3Verifier


class TestMP3Verifier:
    """Tests for MP3Verifier class."""

    @pytest.fixture
    def verifier(self):
        """Create verifier instance."""
        return MP3Verifier()

    def test_verify_detects_id3v2_tag(self, verifier: MP3Verifier):
        """Test detection of ID3v2 tag at file start."""
        # ID3v2 header: "ID3" + version + flags + size
        id3v2_data = b"ID3\x04\x00\x00\x00\x00\x00\x00" + b"\x00" * 100
        result = verifier.verify(id3v2_data)

        assert not result.passed
        assert any("ID3v2" in issue for issue in result.issues)

    def test_verify_detects_id3v1_tag(self, verifier: MP3Verifier):
        """Test detection of ID3v1 tag at file end."""
        # Create data with ID3v1 tag (128 bytes starting with "TAG")
        main_data = b"\xff\xfb\x90\x00" + b"\x00" * 100  # MP3 frame header + data
        id3v1_tag = b"TAG" + b"\x00" * 125  # 128 byte ID3v1 tag
        data = main_data + id3v1_tag

        result = verifier.verify(data)

        assert not result.passed
        assert any("ID3v1" in issue for issue in result.issues)

    def test_verify_no_mp3_frame(self, verifier: MP3Verifier):
        """Test handling of data with no valid MP3 frame."""
        invalid_data = b"\x00" * 100

        result = verifier.verify(invalid_data)

        assert not result.passed
        assert any("frame sync" in issue.lower() for issue in result.issues)

    def test_verify_valid_mp3_header(self, verifier: MP3Verifier):
        """Test valid MP3 header detection.

        MP3 frame header (32 bits):
        - Sync: 11 bits (all 1s)
        - Version: 2 bits (11 = MPEG1)
        - Layer: 2 bits (01 = Layer III)
        - Protection: 1 bit
        - Bitrate: 4 bits
        - Sample rate: 2 bits (00 = 44100Hz for MPEG1)
        - Padding: 1 bit
        - Private: 1 bit
        - Channel mode: 2 bits (11 = mono)
        - etc.

        For 44100Hz mono MP3:
        0xFF 0xFB 0x90 0xC0 = MPEG1 Layer III, 128kbps, 44100Hz, mono
        """
        # Valid MPEG1 Layer III, 44100Hz, mono header
        # 0xFF = sync (first 8 bits)
        # 0xFB = sync + MPEG1 + Layer III + no protection
        # 0x90 = 128kbps + 44100Hz + no padding
        # 0xC0 = mono + mode extension + copyright + original
        valid_mp3 = bytes([0xFF, 0xFB, 0x90, 0xC0]) + b"\x00" * 100

        result = verifier.verify(valid_mp3)

        # Should pass all checks
        assert result.passed
        assert len(result.issues) == 0
