"""MP3 format verification."""

import logging
import struct

from audio_generation.domain.models import VerificationResult
from audio_generation.domain.constants import TARGET_SAMPLE_RATE


class MP3Verifier:
    """Verifies MP3 format meets requirements.

    Checks that output meets specifications:
    - Format: MP3 (MPEG Audio Layer III)
    - Channels: Mono (1 channel)
    - Sample Rate: 44100 Hz
    - ID3v1: NOT present
    - ID3v2: NOT present
    """

    def verify(self, mp3_data: bytes) -> VerificationResult:
        """Verify MP3 meets required format specifications.

        Args:
            mp3_data: MP3 file bytes

        Returns:
            VerificationResult with passed status and any issues
        """
        issues = []

        # Check for ID3v2 tag at start
        if mp3_data[:3] == b"ID3":
            issues.append("ID3v2 tag present at start of file")

        # Check for ID3v1 tag at end
        if len(mp3_data) >= 128 and mp3_data[-128:-125] == b"TAG":
            issues.append("ID3v1 tag present at end of file")

        # Find first MP3 frame to verify format
        # MP3 frame sync: 11 bits set (0xFF followed by 0xE0 or higher)
        frame_start = -1
        for i in range(len(mp3_data) - 4):
            if mp3_data[i] == 0xFF and (mp3_data[i + 1] & 0xE0) == 0xE0:
                frame_start = i
                break

        if frame_start == -1:
            issues.append("No valid MP3 frame sync found")
            return VerificationResult(passed=False, issues=issues)

        # Parse MP3 frame header (4 bytes)
        header = struct.unpack(">I", mp3_data[frame_start : frame_start + 4])[0]

        # Extract fields from header
        # Bits 19-20: MPEG version (11 = MPEG1, 10 = MPEG2, 00 = MPEG2.5)
        version_bits = (header >> 19) & 0x03
        # Bits 17-18: Layer (01 = Layer III)
        layer_bits = (header >> 17) & 0x03
        # Bits 10-11: Sample rate index
        sample_rate_index = (header >> 10) & 0x03
        # Bit 6: Channel mode (00-10 = stereo variants, 11 = mono)
        channel_mode = (header >> 6) & 0x03

        # Verify Layer III
        if layer_bits != 0x01:
            issues.append(f"Not MP3 Layer III (layer bits: {layer_bits})")

        # Sample rate lookup table
        sample_rates = {
            0x03: {0: 44100, 1: 48000, 2: 32000},  # MPEG1
            0x02: {0: 22050, 1: 24000, 2: 16000},  # MPEG2
            0x00: {0: 11025, 1: 12000, 2: 8000},  # MPEG2.5
        }

        if (
            version_bits in sample_rates
            and sample_rate_index in sample_rates[version_bits]
        ):
            actual_rate = sample_rates[version_bits][sample_rate_index]
            if actual_rate != TARGET_SAMPLE_RATE:
                issues.append(
                    f"Sample rate is {actual_rate}Hz, expected {TARGET_SAMPLE_RATE}Hz"
                )
        else:
            issues.append(
                f"Unable to determine sample rate (version: {version_bits}, index: {sample_rate_index})"
            )

        # Verify mono (channel mode 11 = single channel)
        if channel_mode != 0x03:
            mode_names = {0: "stereo", 1: "joint stereo", 2: "dual channel", 3: "mono"}
            issues.append(
                f"Channel mode is {mode_names.get(channel_mode, 'unknown')}, expected mono"
            )

        passed = len(issues) == 0

        if passed:
            logging.info("MP3 format verification: PASSED")
        else:
            logging.warning(f"MP3 format verification: FAILED ({len(issues)} issues)")
            for issue in issues:
                logging.warning(f"  - {issue}")

        return VerificationResult(passed=passed, issues=issues)
