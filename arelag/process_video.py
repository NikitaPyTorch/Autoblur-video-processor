import argparse
import os
import subprocess
import sys
import tempfile
import traceback
from pathlib import Path

import cv2
import numpy as np
from moviepy import AudioFileClip, CompositeVideoClip, ImageClip, VideoFileClip


def apply_blur(frame: np.ndarray, sigma: float) -> np.ndarray:
    return cv2.GaussianBlur(frame, (0, 0), sigmaX=sigma, sigmaY=sigma)


def apply_sweet_effect(
    input_wav: Path, output_wav: Path, semitones: float = 1.5
) -> None:
    """Sweet audio effect via FFmpeg: pitch shift + warmth + compression."""
    # Pitch shift factor: 2^(semitones/12)
    pitch_factor = 2 ** (semitones / 12.0)
    # atempo compensates speed change from asetrate (must be between 0.5 and 2.0)
    tempo_factor = 1.0 / pitch_factor

    # FFmpeg filter chain:
    # asetrate: changes pitch by resampling (also changes speed)
    # atempo: corrects speed back to original
    # lowpass: warmth — roll off harsh highs from pitch shift
    # acompressor: light compression for polished sound
    # loudnorm: normalize loudness
    filter_chain = (
        f"asetrate=44100*{pitch_factor},"
        f"atempo={tempo_factor},"
        f"aresample=44100,"
        f"lowpass=f=8000,"
        f"acompressor=threshold=-20dB:ratio=2:attack=5:release=50,"
        f"loudnorm=I=-16:TP=-1.5:LRA=11"
    )

    cmd = [
        "ffmpeg", "-y",
        "-i", str(input_wav),
        "-af", filter_chain,
        "-ar", "44100",
        "-ac", "2",
        str(output_wav),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"FFmpeg error:\n{result.stderr}", file=sys.stderr, flush=True)
        raise RuntimeError("FFmpeg audio processing failed")


def process_video(
    video_path: str,
    disclaimer_path: str,
    output_path: str,
    blur_sigma: float,
    pitch_semitones: float,
    overlay_duration: float,
) -> None:
    video = VideoFileClip(video_path)

    with tempfile.TemporaryDirectory() as td:
        td = Path(td)
        raw_wav = td / "audio_raw.wav"
        sweet_wav = td / "audio_sweet.wav"

        # Step 1: Process audio
        processed_audio = None
        if video.audio is not None:
            print("[1/4] Extracting audio...", flush=True)
            video.audio.write_audiofile(
                str(raw_wav), fps=44100, nbytes=2, codec="pcm_s16le"
            )
            print("[2/4] Applying sweet audio effect...", flush=True)
            apply_sweet_effect(raw_wav, sweet_wav, semitones=pitch_semitones)
            processed_audio = AudioFileClip(str(sweet_wav))

        # Step 2: Apply blur to all frames
        print("[3/4] Applying blur + compositing disclaimer...", flush=True)
        blurred = video.image_transform(
            lambda frame: apply_blur(frame, sigma=blur_sigma)
        )

        # Step 3: Disclaimer overlay for first N seconds
        dur = min(overlay_duration, video.duration)
        disclaimer = (
            ImageClip(disclaimer_path)
            .with_duration(dur)
            .resized(new_size=(video.size[0], video.size[1]))
            .with_start(0)
            .with_position(("center", "center"))
        )

        composed = CompositeVideoClip([blurred, disclaimer])

        # Step 4: Attach processed audio and write
        if processed_audio is not None:
            composed = composed.with_audio(
                processed_audio.with_duration(video.duration)
            )

        print("[4/4] Writing output video...", flush=True)
        composed.write_videofile(
            output_path,
            codec="libx264",
            audio_codec="aac",
            audio_bitrate="192k",
            fps=video.fps,
            threads=os.cpu_count() or 4,
        )

    video.close()


def main():
    parser = argparse.ArgumentParser(description="Video editing pipeline")
    parser.add_argument("--video", required=True, help="Input .mp4 video path")
    parser.add_argument("--disclaimer", required=True, help="Disclaimer image path")
    parser.add_argument("--output", default="output.mp4", help="Output video path")
    parser.add_argument(
        "--blur-sigma", type=float, default=15.0, help="Gaussian blur sigma"
    )
    parser.add_argument(
        "--pitch-semitones",
        type=float,
        default=1.5,
        help="Pitch shift in semitones for sweet effect",
    )
    parser.add_argument(
        "--overlay-duration",
        type=float,
        default=5.0,
        help="Disclaimer overlay duration in seconds",
    )
    args = parser.parse_args()

    try:
        process_video(
            video_path=args.video,
            disclaimer_path=args.disclaimer,
            output_path=args.output,
            blur_sigma=args.blur_sigma,
            pitch_semitones=args.pitch_semitones,
            overlay_duration=args.overlay_duration,
        )
        print("Done!", flush=True)
    except Exception:
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
