
# pdf2vid

internal tool
extensive caching
no error handling

## Requirements

The following tools are required:

1. [Python version 3.12](https://www.python.org).
1. [FFmpeg](https://www.ffmpeg.org).
1. [ImageMagick](https://imagemagick.org).

### Installation (MacOs)

Install [HomeBrew](https://brew.sh/), and run the following commands in a terminal.

```bash
brew install ffmpeg imagemagick ghostscript
pip install -r requirements.txt
```

## Usage (MacOs)

The basic structure of a video is:

1. **Scene** — the smallest unit, covering a single piece of voice-over text.
1. **Chapter** - a group of related scenes covering one topic.
1. **Video** - the full piece, made up of chapters.

All three can be generated independently using the provided tools. Before diving into them, the required environment variables need to be set:

```bash
export MAGICK_HOME=$(brew --prefix imagemagick)
export MAGICK_GS_PATH=/opt/homebrew/bin/gs
export PYTORCH_ENABLE_MPS_FALLBACK=1
```

The tools are now ready for use.

### Generating scenes

Configuration:

```json
{
    "chapter": "C1",
    "scene": "S1",
    "voice":
    {
        "text": "Hello and welcome!",
        "speed": 1.0,
        "delay": 0.0
    },
    "frames":
    {
        "source": "frames.pdf",
        "start": 10,
        "end": 20,
        "duplications": "10:5,15:3,20:1",
        "rate": 10
    }
}
```

Options:

* **chapter** — the ID of the chapter this scene belongs to.
* **scene** — the ID of the scene.
* **voice** — voice-over options:
  * **text** — the text to convert to speech.
  * **speed** — the read-speed.
  * **delay** — the delay in seconds before start playing.
* **frames** — frames options:
  * **source** — the path to the PDF file containing the frames.
  * **start** — the start frame (page) to use for this scene starting from 1 (optional, default 0).
  * **end** — the end frame (page) to use for this scene (optional, default last frame).
  * **duplications** — specifies which frames need to be duplicated (optional, see instructions below).
  * **rate** — the framerate (optional, default: 10).

Duplication is very useful for pausing frames. Its need to be specified in the following format: `frame_number:amount`. Multiple duplications can be specified by separating the with a comma `,`.

Generation:

```bash
python path/to/tools/generate.py --type "scene" --config "config.json" --output "dist"
```

Arguments:

* **--config** — path the scene configuration file.
* **--output** — the root directory of the output.

Result:

```txt
dist
|- cache
|  | -C1
|  |  |- cache
|  |  |  |- S1
|  |  |  |  |- _frames (frames with duplications)
|  |  |  |  |- frames (extracted frames from the PDF)
|  |  |  |  |- config.json (copy of the previous config)
|  |  |  |  |- video.mp4 (generated video from the frames)
|  |  |  |  |- voice.wav (generated voice-over)
|  |  |- S1.mp4 (final result with video and voice combined)
```

**Note** that this will only generate a new result if one of the configuration options has changed.

### Generate chapter

Configuration:

```json
{
    "chapter": "C1",
    "description": "First chapter",
    "scenes": ["S1", "S2", "S3"]
}
```

Options:

* **chapter** — the ID of the chapter.
* **description** — the description of the topic (for yourself, not used by the tools).
* **scenes** — the list of scene IDs in rendering order.

Generation:

```bash
python path/to/tools/generate.py --type "chapter" --config "config.json" --output "dist"
```

Arguments:

* **--config** — path the scene configuration file.
* **--output** — the root directory of the output.

Result:

```txt
dist
|- cache
|  | -C1
|  |  |- cache
|  |  |- S1.mp4
|  |  |- S2.mp4
|  |  |- S3.mp4
|  |  |- playlist.txt (list of all mp4 scene files in correct order)
|- C1.mp4 (final result with all scenes combined)
```

**Note** that this will always generate a new result.

### Generate video

Configuration:

```json
{
    "video": "Instructions",
    "description": "The most clear video ever",
    "chapters": ["C1", "C2"]
}
```

Options:

* **video** — the name of the video.
* **chapters** — the list of chapter IDs in rendering order.

Generation:

```bash
python path/to/tools/generate.py --type "video" --config "config.json" --output "dist"
```

Arguments:

* **--config** — path the scene configuration file.
* **--output** — the root directory of the output.

Result:

```txt
dist
|- cache
|  |- C1.mp4
|  |- C2.mp4
|  |- playlist.txt (list of all mp4 chapter files in correct order)
|- Instructions.mp4 (final result with all chapters combined)
```

**Note** that this will always generate a new result.
