
from ..models.scene import VoiceOptions, FrameOptions, FolderPaths, FilePaths, Config

from ..utils.config import read_config
from ..utils.filesystem import get_parent_path, join_paths, path_exists, copy_file, remove_file, create_folder, remove_folder
from ..utils.hashing import file_hash_changed, write_file_hash

### DEFAULTS ##########################

CHAPTER_DEFAULT = "C1"
SCENE_DEFAULT = "S1"
VOICE_DEFAULTS = { "speed": 1.0, "delay": 0.0 }
FRAMES_DEFAULTS = { "start": None, "end": None, "duplications": "", "rate": 10 }

### PROCESS ##########################

def generate_scene(chapter_id, scene_id, config_file, output_folder):

    config = _create_config(chapter_id, scene_id, config_file, output_folder)
    
    updated = _initialize(config)

    if not updated:
        return False
    
    _generate(config)
    _finalize(config)

    return True

### CONFIG ##########################

def _read_config_data(config_file):

    data = read_config(config_file)

    if data == None:
        return None

    data["voice"] = VOICE_DEFAULTS | data["voice"]
    data["frames"] = FRAMES_DEFAULTS | data["frames"]

    return data

def _create_config(chapter_id, scene_id, config_file, output_folder):

    data = _read_config_data(config_file)

    if data == None:
        raise RuntimeError(f"Configuration not found for scene {chapter_id}:{scene_id}!")

    voice = _create_voice_options(data)
    frames = _create_frame_options(data)
    folders = _create_folder_paths(config_file, output_folder, chapter_id, scene_id)
    files = _create_file_paths(config_file, scene_id, folders)

    return Config(
        chapter = chapter_id,
        scene = scene_id,
        voice = voice,
        frames = frames,
        folders = folders,
        files = files
    )

def _create_voice_options(data):

    voice = data.get("voice")

    return VoiceOptions(
        text = voice.get("text"),
        speed = voice.get("speed"),
        delay = voice.get("delay")
    )

def _create_frame_options(data):

    frames = data.get("frames")

    return FrameOptions(
        source = frames.get("source"),
        start = frames.get("start"),
        end = frames.get("end"),
        duplications = frames.get("duplications"),
        rate = frames.get("rate")
    )

def _create_folder_paths(config_file, output_folder, chapter_id, scene_id):

    config_folder = get_parent_path(config_file)
    chapter_folder = join_paths(output_folder, "chapters", chapter_id)
    scene_folder = join_paths(chapter_folder, "scenes", scene_id)
    frames_folder = join_paths(scene_folder, "frames")
    duplications_folder = join_paths(scene_folder, "_frames")

    return FolderPaths(
        config = config_folder,
        chapter = chapter_folder,
        scene = scene_folder,
        frames = frames_folder,
        duplications = duplications_folder
    )

def _create_file_paths(config_file, scene_id, folders):

    cache_file = join_paths(folders.scene, "config.json")
    voice_file = join_paths(folders.scene, "voice.wav")
    frames_file = join_paths(folders.scene, "frames.md5")
    video_file = join_paths(folders.scene, "video.mp4")
    result_file = join_paths(folders.chapter, f"{scene_id}.mp4")

    return FilePaths(
        source = config_file,
        cache = cache_file,
        voice = voice_file,
        frames = frames_file,
        video = video_file,
        result = result_file
    )

### INITIALIZE ##########################

def _initialize(config):

    already_existed = _assure_folders(config)

    if already_existed:
        return _update_cache(config)

    return True

def _assure_folders(config):

    if not path_exists(config.folders.scene):
        create_folder(config.folders.scene)
        return False
    
    return True

def _update_cache(config):

    cached_config = _read_config_data(config.files.cache)

    if cached_config == None:
        return True
    
    cached_voice = _create_voice_options(cached_config)
    cached_frames = _create_frame_options(cached_config)

    voice_text_changed = cached_voice.text != config.voice.text
    voice_speed_changed = cached_voice.speed != config.voice.speed
    voice_delay_changed = cached_voice.delay != config.voice.delay

    frames_pdf_file = join_paths(config.folders.config, config.frames.source)

    frames_hash_changed = file_hash_changed(frames_pdf_file, config.files.frames)
    frames_source_changed = cached_frames.source != config.frames.source
    frames_start_changed = cached_frames.start != config.frames.start
    frames_end_changed = cached_frames.end != config.frames.end
    frames_duplications_changed = cached_frames.duplications != config.frames.duplications
    frames_rate_changed = cached_frames.rate != config.frames.rate

    voice_changed = voice_text_changed or voice_speed_changed or voice_delay_changed
    frames_changed = frames_hash_changed or frames_source_changed or frames_start_changed or frames_end_changed

    video_changed = frames_rate_changed
    result_changed = False

    if voice_changed:
        remove_file(config.files.voice)
        result_changed = True
    
    if frames_changed:
        remove_folder(config.folders.frames)
        frames_duplications_changed = True
    
    if frames_duplications_changed:
        remove_folder(config.folders.duplications)
        video_changed = True
    
    if video_changed:
        remove_file(config.files.video)
        result_changed = True

    if result_changed:
        remove_file(config.files.result)

    return result_changed

### GENERATE ##########################

def _generate(config):

    print(f"‣ GENERATING SCENE {config.chapter}:{config.scene}")

    _voiceover(config)
    _frames(config)
    _duplications(config)
    _video(config)
    _result(config)

def _voiceover(config):

    files = config.files
    options = config.voice
    
    if path_exists(files.voice):
        return
    
    print("  ⧗ Generating voice", end="\r", flush=True)

    from ..tasks.generate_voice import generate_voice

    generate_voice(options.text, options.speed, options.delay, files.voice)

    print(f"  ✔ Generated voice -> {files.voice}")

def _frames(config):

    folders = config.folders
    files = config.files
    options = config.frames

    if path_exists(folders.frames):
        return
    
    print("  ⧗ Extracting frames", end="\r", flush=True)

    create_folder(folders.frames)
    pdf_file = join_paths(folders.config, options.source)

    from ..tasks.extract_frames import extract_frames

    extract_frames(pdf_file, folders.frames, options.start, options.end)

    write_file_hash(pdf_file, files.frames)

    print(f"  ✔ Extracted frames -> {folders.frames}")

def _duplications(config):

    folders = config.folders
    options = config.frames

    if path_exists(folders.duplications):
        return
    
    print("  ⧗ Duplicating frames", end="\r", flush=True)

    create_folder(folders.duplications)

    from ..tasks.duplicate_frames import duplicate_frames

    duplicate_frames(folders.frames, folders.duplications, options.duplications)

    print(f"  ✔ Duplicated frames -> {folders.duplications}")

def _video(config):

    folders = config.folders
    files = config.files
    options = config.frames

    if path_exists(files.video):
        return
    
    print("  ⧗ Creating video", end="\r", flush=True)

    from ..tasks.create_video import create_video

    create_video(folders.duplications, files.video, options.rate)

    print(f"  ✔ Created video -> {files.video}")

def _result(config):

    files = config.files

    if path_exists(files.result):
        return
    
    print("  ⧗ Combining video and voice", end="\r", flush=True)

    from ..tasks.add_audio import add_audio

    add_audio(files.video, files.voice, files.result)

    print(f"  ✔ Combined video and voice -> {files.result}")

### FINALIZE ##########################

def _finalize(config):

    files = config.files

    copy_file(files.source, files.cache)
