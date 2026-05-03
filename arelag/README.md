# Bluring Script

Bluring Script is a small video-processing command-line tool. It takes an input video, applies a Gaussian blur, overlays a disclaimer image at the start, and applies a pitch and warmth effect to the video's audio.

## Requirements

- Python 3.11+
- FFmpeg available on your `PATH`
- Docker, if you prefer to run the tool in a container

## Run With Docker

Build the image from the repository root:

```sh
docker build -t arelag .
```

Run the processor by mounting the current directory into the container:

```sh
docker run --rm -v "$PWD:/media" arelag \
  --video "/media/input.mov" \
  --disclaimer "/media/disclaimer.jpg" \
  --output "/media/output.mov"
```

Replace `input.mov` and `disclaimer.jpg` with files in your local checkout. Generated videos are ignored by git by default.

## Run Locally

Create and activate a virtual environment:

```sh
python3 -m venv .venv
source .venv/bin/activate
```

Install dependencies:

```sh
pip install -r requirements.txt
```

Run the script:

```sh
python process_video.py \
  --video input.mov \
  --disclaimer disclaimer.jpg \
  --output output.mov
```

## Options

- `--video`: required path to the input video.
- `--disclaimer`: required path to the disclaimer image.
- `--output`: output video path. Defaults to `output.mp4`.
- `--blur-sigma`: Gaussian blur strength. Defaults to `15.0`.
- `--pitch-semitones`: audio pitch shift amount. Defaults to `1.5`.
- `--overlay-duration`: number of seconds to show the disclaimer image. Defaults to `5.0`.
