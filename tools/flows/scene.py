
from tasks.generate_voice import generate_voice
from tasks.extract_frames import extract_frames
from tasks.duplicate_frames import duplicate_frames
from tasks.create_video import create_video
from tasks.add_audio import add_audio

from models.scene import VoiceOptions, FrameOptions, FolderPaths, FilePaths, Config

from utils.config import read_config
from utils.filesystem import join_paths, path_exists, copy_file, remove_file, create_folder, remove_folder

### DEFAULTS ##########################

CHAPTER_DEFAULT = "C1"
SCENE_DEFAULT = "S1"
VOICE_DEFAULTS = { "speed": 1.0, "delay": 0.0 }
FRAMES_DEFAULTS = { "start": None, "end": None, "duplications": "", "rate": 10 }

### PROCESS ##########################

def generate_scene(config_file, output_folder):

    config = _create_config(config_file, output_folder)

    no_changes = _initialize(config)

    if no_changes:
        print("✔ No changes detected")
        return
    
    _generate(config)
    _finalize(config_file, config)

### CONFIG ##########################

def _create_config(config_file, output_folder):

    data = _read_config_data(config_file)

    chapter = data.get("chapter", CHAPTER_DEFAULT)
    scene = data.get("scene", SCENE_DEFAULT)
    voice = _create_voice_options(data)
    frames = _create_frame_options(data)
    folders = _create_folder_paths(output_folder, chapter, scene)
    files = _create_file_paths(scene, folders)

    return Config(
        chapter = chapter,
        scene = scene,
        voice = voice,
        frames = frames,
        folders = folders,
        files = files
    )

def _read_config_data(config_file):

    data = read_config(config_file)

    if data == None:
        return None

    data["voice"] = VOICE_DEFAULTS | data["voice"]
    data["frames"] = FRAMES_DEFAULTS | data["frames"]

    return data

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

def _create_folder_paths(output_folder, chapter, scene):

    chapter_folder = join_paths(output_folder, "cache", chapter)
    scene_folder = join_paths(chapter_folder, "cache", scene)
    frames_folder = join_paths(scene_folder, "frames")
    duplications_folder = join_paths(scene_folder, "_frames")

    return FolderPaths(
        chapter = chapter_folder,
        scene = scene_folder,
        frames = frames_folder,
        duplications = duplications_folder
    )

def _create_file_paths(scene, folders):

    config_file = join_paths(folders.scene, "config.json")
    voice_file = join_paths(folders.scene, "voice.wav")
    video_file = join_paths(folders.scene, "video.mp4")
    result_file = join_paths(folders.chapter, f"{scene}.mp4")

    return FilePaths(
        config = config_file,
        voice = voice_file,
        video = video_file,
        result = result_file
    )

### INITIALIZE ##########################

def _initialize(config):

    already_existed = _assure_folders(config)

    if already_existed:
        return _update_cache(config)

    return False

def _assure_folders(config):

    if not path_exists(config.folders.scene):
        create_folder(config.folders.scene)
        return False
    
    return True

def _update_cache(config):

    cached_config = _read_config_data(config.files.config)

    if cached_config == None:
        return False
    
    cached_voice = _create_voice_options(cached_config)
    cached_frames = _create_frame_options(cached_config)

    voice_text_changed = cached_voice.text != config.voice.text
    voice_speed_changed = cached_voice.speed != config.voice.speed
    voice_delay_changed = cached_voice.delay != config.voice.delay

    frames_source_changed = cached_frames.source != config.frames.source
    frames_start_changed = cached_frames.start != config.frames.start
    frames_end_changed = cached_frames.end != config.frames.end
    frames_duplications_changed = cached_frames.duplications != config.frames.duplications
    frames_rate_changed = cached_frames.rate != config.frames.rate

    video_changed = frames_rate_changed
    result_changed = voice_delay_changed

    if voice_text_changed or voice_speed_changed:
        remove_file(config.files.voice)
        result_changed = True
    
    if frames_source_changed or frames_start_changed or frames_end_changed:
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

    return not result_changed

### GENERATE ##########################

def _generate(config):

    _voiceover(config.voice, config.files)
    _frames(config.frames, config.folders)
    _duplications(config.frames, config.folders)
    _video(config.frames, config.folders, config.files)
    _result(config.voice, config.files)

def _voiceover(options, files):

    if path_exists(files.voice):
        return
    
    print("∞ GENERATING VOICE")

    generate_voice(options.text, options.speed, files.voice)

    print(f"✔ GENERATED -> {files.voice}")

def _frames(options, folders):

    if path_exists(folders.frames):
        return
    
    print("∞ EXTRACTING FRAMES")

    create_folder(folders.frames)
    extract_frames(options.source, folders.frames, options.start, options.end)

    print(f"✔ EXTRACTED -> {folders.frames}")

def _duplications(options, folders):

    if path_exists(folders.duplications):
        return
    
    print("∞ DUPLICATING FRAMES")

    create_folder(folders.duplications)
    duplicate_frames(folders.frames, folders.duplications, options.duplications)

    print(f"✔ DUPLICATED -> {folders.duplications}")

def _video(frame_options, folders, files):

    if path_exists(files.video):
        return
    
    print("∞ CREATING VIDEO")

    create_video(folders.duplications, files.video, frame_options.rate)

    print(f"✔ CREATED -> {files.video}")

def _result(voice_options, files):

    if path_exists(files.result):
        return
    
    print("∞ COMBINING VIDEO AND VOICE")

    add_audio(files.video, files.voice, voice_options.delay, files.result)

    print(f"✔ COMBINED -> {files.result}")

### FINALIZE ##########################

def _finalize(config_file, config):

    copy_file(config_file, config.files.config)
