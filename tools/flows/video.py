
from ..models.video import FolderPaths, FilePaths, Config

from ..utils.config import read_config
from ..utils.filesystem import get_parent_path, join_paths, path_exists, copy_file, create_folder

### DEFAULTS ##########################

VIDEO_DEFAULT = "Video"
DESCRIPTION_DEFAULT = ""
CHAPTERS_DEFAULT = []

### PROCESS ##########################

def generate_video(config_file, output_folder, chapter_id, scene_id):

    config = _create_config(config_file, output_folder)

    if chapter_id != None:
        return _generate_chapter(config, chapter_id, scene_id)

    return _generate_video(config)

### CONFIG ##########################

def _create_config(config_file, output_folder):

    data = read_config(config_file)

    video = data.get("video", VIDEO_DEFAULT)
    description = data.get("description", DESCRIPTION_DEFAULT)
    chapters = data.get("chapters", CHAPTERS_DEFAULT)
    folders = _create_folder_paths(config_file, output_folder)
    files = _create_file_paths(config_file, video, folders)

    return Config(
        video = video,
        description = description,
        chapters = chapters,
        folders = folders,
        files = files
    )

def _create_folder_paths(config_file, output_folder):

    config_folder = get_parent_path(config_file)
    cache_folder = join_paths(output_folder, "chapters")

    return FolderPaths(
        config = config_folder,
        output = output_folder,
        cache = cache_folder
    )

def _create_file_paths(config_file, video, folders):

    cache_file = join_paths(folders.output, "config.json")
    result_file = join_paths(folders.output, f"{video}.mp4")

    return FilePaths(
        source = config_file,
        cache = cache_file,
        result = result_file
    )

### PROCESS ##########################

def _generate_chapter(config, chapter_id, scene_id):

    from .chapter import generate_chapter

    chapter_config = config.chapters.get(chapter_id)
    output_folder = config.folders.output
    config_folder = config.folders.config

    config_file = join_paths(config_folder, chapter_config)

    updated = generate_chapter(chapter_id, config_file, output_folder, scene_id)

    if not updated and scene_id == None:
        print(f"✔ CHAPTER {chapter_id} UP-TO-DATE")
    
    return updated

def _generate_video(config):

    config_updated = _initialize(config)
    chapters_updated = _chapters(config)

    updated = config_updated or chapters_updated

    if not updated:
        print(f"✔ VIDEO UP-TO-DATE")
        return False

    _video(config)
    _finalize(config)

    return True

def _initialize(config):

    already_existed = _assure_folders(config)

    if already_existed:
        return _update_cache(config)

    return True

def _assure_folders(config):

    if not path_exists(config.folders.cache):
        
        create_folder(config.folders.cache)
        return False
    
    return True

def _update_cache(config):

    cached_config = read_config(config.files.cache)

    if cached_config == None:
        return True
    
    scenes_changed = cached_config["chapters"] != config.chapters

    return scenes_changed

def _chapters(config):

    from .chapter import generate_chapter

    chapter_items = config.chapters.items()
    output_folder = config.folders.output
    config_folder = config.folders.config

    video_updated = False

    for chapter_id, chapter_config in chapter_items:

        config_file = join_paths(config_folder, chapter_config)
        chapter_updated = generate_chapter(chapter_id, config_file, output_folder, None)

        if chapter_updated:
            video_updated = True

    return video_updated

def _video(config):

    print("⧗ GENERATING VIDEO", end="\r", flush=True)

    from ..tasks.stitch_videos import stitch_videos
    
    cache_folder = config.folders.cache
    chapter_keys = config.chapters.keys()
    result_file = config.files.result

    stitch_videos(cache_folder, chapter_keys, result_file)

    print(f"✔ GENERATED VIDEO -> {config.files.result}")

def _finalize(config):

    copy_file(config.files.source, config.files.cache)
