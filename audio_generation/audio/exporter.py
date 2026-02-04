"""MP3 exporter with ID3 tag stripping."""

import io
import logging
from pathlib import Path

from pydub import AudioSegment

from audio_generation.domain.constants import TARGET_CHANNELS, TARGET_SAMPLE_RATE


class MP3Exporter:
    """Exports AudioSegment to MP3 format.

    Handles the final export to MP3 with proper format specifications
    and ID3 tag removal.
    """

    def export(self, audio: AudioSegment, output_path: Path) -> bytes:
        """Export audio to MP3 with ID3 tags stripped.

        Ensures output meets requirements:
        - Format: MP3 (MPEG Audio Layer III)
        - Channels: Mono (1 channel)
        - Sample Rate: 44100 Hz
        - ID3 Tags: NOT present

        Args:
            audio: AudioSegment to export
            output_path: Output file path

        Returns:
            MP3 data bytes
        """
        # Ensure correct format (mono, 44100Hz)
        if audio.frame_rate != TARGET_SAMPLE_RATE:
            audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)
        if audio.channels != TARGET_CHANNELS:
            audio = audio.set_channels(TARGET_CHANNELS)

        # Export to MP3 without ID3 tags
        mp3_buffer = io.BytesIO()
        audio.export(
            mp3_buffer,
            format="mp3",
            parameters=["-id3v2_version", "0"],
        )

        mp3_data = mp3_buffer.getvalue()

        # Strip any remaining ID3 tags
        mp3_data = self._strip_id3_tags(mp3_data)

        # Ensure output directory exists and save
        output_path.parent.mkdir(parents=True, exist_ok=True)
        output_path.write_bytes(mp3_data)

        logging.info(f"Exported audio to: {output_path}")
        logging.info(
            f"Total duration: {len(audio)}ms, File size: {len(mp3_data):,} bytes"
        )

        return mp3_data

    def export_to_bytes(self, audio: AudioSegment) -> bytes:
        """Export audio to MP3 bytes without writing to file.

        Args:
            audio: AudioSegment to export

        Returns:
            MP3 data bytes
        """
        # Ensure correct format (mono, 44100Hz)
        if audio.frame_rate != TARGET_SAMPLE_RATE:
            audio = audio.set_frame_rate(TARGET_SAMPLE_RATE)
        if audio.channels != TARGET_CHANNELS:
            audio = audio.set_channels(TARGET_CHANNELS)

        # Export to MP3 without ID3 tags
        mp3_buffer = io.BytesIO()
        audio.export(
            mp3_buffer,
            format="mp3",
            parameters=["-id3v2_version", "0"],
        )

        mp3_data = mp3_buffer.getvalue()

        # Strip any remaining ID3 tags
        return self._strip_id3_tags(mp3_data)

    def _strip_id3_tags(self, mp3_data: bytes) -> bytes:
        """Remove ID3v1 and ID3v2 tags from MP3 data.

        ID3v2: Variable size at start, starts with "ID3"
        ID3v1: 128 bytes at end, starts with "TAG"

        Args:
            mp3_data: MP3 file bytes

        Returns:
            MP3 data with all ID3 tags removed
        """
        data = bytearray(mp3_data)

        # Strip ID3v2 (at beginning)
        while data[:3] == b"ID3":
            # ID3v2 header: "ID3" + 2 version bytes + 1 flags byte + 4 size bytes
            if len(data) < 10:
                break

            # Size is stored as syncsafe integer (7 bits per byte)
            size_bytes = data[6:10]
            size = (
                (size_bytes[0] & 0x7F) << 21
                | (size_bytes[1] & 0x7F) << 14
                | (size_bytes[2] & 0x7F) << 7
                | (size_bytes[3] & 0x7F)
            )

            # Total header size = 10 (header) + size (tag data)
            total_size = 10 + size
            logging.debug(f"Stripping ID3v2 tag: {total_size} bytes")
            data = data[total_size:]

        # Strip ID3v1 (at end) - always 128 bytes starting with "TAG"
        if len(data) >= 128 and data[-128:-125] == b"TAG":
            logging.debug("Stripping ID3v1 tag: 128 bytes")
            data = data[:-128]

        return bytes(data)
