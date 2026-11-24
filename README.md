
# pdf2vid

Simple tool for creating videos from PDF files with AI-generated voice-overs.

🎥 [Example video](https://www.youtube.com/watch?v=BMgJ4wZbCWg)

⚙️ [Example source](https://github.com/MaskingTechnology/jitar/tree/main/videos/introduction)

**Note:** This is currently developed as an internal tool with a “works for us” mindset. You’re free to use it, as long as you’re not expecting a polished solution (input validation and error handling are minimal). Treat it nicely, and it will treat you nicely too.

## Requirements

The following tools need to be installed on your machine:

1. [Python version 3.12](https://www.python.org).
1. [HomeBrew](https://brew.sh/).

### Installation (MacOs)

Run the following commands in a terminal.

```bash
brew install ffmpeg poppler
python -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt
```

## Usage (MacOs)

The basic structure of a video is:

1. **Video** - the full piece, made up of chapters.
1. **Chapter** - a group of related scenes covering one topic.
1. **Scene** — the smallest unit, covering a single piece of voice-over text.

All three can be generated independently using the provided tool.

### Video

Configuration: `video.json`

```json
{
    "video": "Instructions",
    "description": "The most clear video ever",
    "chapters": {
        "C1": "chapter1.json",
        "C2": "chapter2.json"
    }
}
```

Options:

* **video** — the name of the video.
* **chapters** — the object of chapter IDs and their configuration files in rendering order.

Generation:

```bash
path/to/pdf2vid --config "config.json" --output "dist"
```

Arguments:

* **--config** — path the video configuration file.
* **--output** — the root directory of the video output.

Result:

```txt
dist
|- chapters (generated chapter videos)
|- config.json (cached video config for change detection)
|- Instructions.mp4 (final result with all chapters combined)
```

### Chapter

Configuration: `chapter1.json`

```json
{
    "description": "First chapter",
    "scenes": {
        "S1": "chapter1/scene1.json",
        "S2": "chapter1/scene2.json",
        "S3": "chapter1/scene3.json"
    }
}
```

Options:

* **description** — the description of the topic (for yourself, not used by the tools).
* **scenes** — the object of scene IDs and their configuration files in rendering order.

Generation:

```bash
path/to/pdf2vid --config "config.json" --output "dist" --chapter "C1"
```

Arguments:

* **--config** — path the video configuration file.
* **--output** — the root directory of the video output.
* **--chapter** — the ID of the chapter to generate.

Result:

```txt
dist
|- chapters
|  |- C1 (generated scene videos)
|  |- C1.mp4 (chapter video)
|- config.json (cached video config for change detection)
|- Instructions.mp4 (final result with all chapters combined)
```

### Scene

Configuration: `chapter1/scene1.json`

```json
{
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
path/to/pdf2vid --config "config.json" --output "dist" --chapter "C1" --scene "S1"
```

Arguments:

* **--config** — path the video configuration file.
* **--output** — the root directory of the video output.
* **--chapter** — the ID of the chapter to generate.
* **--scene** — the ID of the scene to generate.

Result:

```txt
dist
|- chapters
|  |- C1
|  |  |- scenes
|  |  |  |- S1
|  |  |  |  |- _frames (frames with duplications)
|  |  |  |  |- frames (extracted frames from the PDF)
|  |  |  |  |- config.json (cached scene config for change detection)
|  |  |  |  |- frames.md5 (PDF file hash for change detection)
|  |  |  |  |- video.mp4 (generated video from the frames)
|  |  |  |  |- voice.wav (generated voice-over)
|  |  |- S1.mp4 (final scene with video and voice combined)
|  |  |- config.json (cached chapter config for change detection)
|  |- C1.mp4 (chapter video)
|- config.json (cached video config for change detection)
|- Instructions.mp4 (final result with all chapters combined)
```
