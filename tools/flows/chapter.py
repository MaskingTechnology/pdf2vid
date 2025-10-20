
from ..models.chapter import FolderPaths, FilePaths, Config

from ..utils.config import read_config
from ..utils.filesystem import get_parent_path, join_paths, path_exists, copy_file, create_folder

### DEFAULTS ##########################

CHAPTER_DEFAULT = "C1"
DESCRIPTION_DEFAULT = ""
SCENES_DEFAULT = []

### PROCESS ##########################

def generate_chapter(chapter_id, config_file, output_folder, scene_id):

    config = _create_config(chapter_id, config_file, output_folder)

    if scene_id != None:
        return _generate_scene(config, scene_id)

    return _generate_chapter(config)

### CONFIG ##########################

def _create_config(chapter_id, config_file, output_folder):

    data = read_config(config_file)

    if data == None:
        raise RuntimeError(f"Configuration not found for chapter {chapter_id}!")

    description = data.get("description", DESCRIPTION_DEFAULT)
    scenes = data.get("scenes", SCENES_DEFAULT)
    folders = _create_folder_paths(config_file, output_folder, chapter_id)
    files = _create_file_paths(config_file, chapter_id, folders)

    return Config(
        chapter = chapter_id,
        description = description,
        scenes = scenes,
        folders = folders,
        files = files
    )

def _create_folder_paths(config_file, output_folder, chapter_id):

    config_folder = get_parent_path(config_file)
    cache_folder = join_paths(output_folder, "chapters")
    chapter_folder = join_paths(cache_folder, chapter_id)

    return FolderPaths(
        config = config_folder,
        output = output_folder,
        cache = cache_folder,
        chapter = chapter_folder
    )

def _create_file_paths(config_file, chapter_id, folders):

    cache_file = join_paths(folders.chapter, "config.json")
    result_file = join_paths(folders.cache, f"{chapter_id}.mp4")

    return FilePaths(
        source = config_file,
        cache = cache_file,
        result = result_file
    )

### PROCESS ##########################

def _generate_scene(config, scene_id):

    chapter_id = config.chapter
    scene_config = config.scenes.get(scene_id)

    if scene_config == None:
        raise RuntimeError(f"Unknown scene {chapter_id}:{scene_id}")
    
    output_folder = config.folders.output
    config_folder = config.folders.config

    config_file = join_paths(config_folder, scene_config)
    
    from .scene import generate_scene

    updated = generate_scene(chapter_id, scene_id, config_file, output_folder)

    if not updated:
        print(f"✔ SCENE {chapter_id}:{scene_id} UP-TO-DATE")
    
    return updated

def _generate_chapter(config):

    config_updated = _initialize(config)
    scenes_updated = _scenes(config)

    updated = config_updated or scenes_updated

    if not updated:
        return False

    _chapter(config)
    _finalize(config)

    return True

def _initialize(config):

    already_existed = _assure_folders(config)

    if already_existed:
        return _update_cache(config)

    return True

def _assure_folders(config):

    if not path_exists(config.folders.chapter):
        
        create_folder(config.folders.chapter)
        return False
    
    return True

def _update_cache(config):

    cached_config = read_config(config.files.cache)

    if cached_config == None:
        return True
    
    scenes_changed = cached_config["scenes"] != config.scenes

    return scenes_changed

def _scenes(config):

    from .scene import generate_scene

    chapter_id = config.chapter
    scene_items = config.scenes.items()
    output_folder = config.folders.output
    config_folder = config.folders.config

    chapter_updated = False

    for scene_id, scene_config in scene_items:

        config_file = join_paths(config_folder, scene_config)
        scene_updated = generate_scene(chapter_id, scene_id, config_file, output_folder)

        if scene_updated:
            chapter_updated = True

    return chapter_updated

def _chapter(config):

    print(f"⧗ GENERATING CHAPTER {config.chapter}", end="\r", flush=True)

    from ..tasks.stitch_videos import stitch_videos

    chapter_folder = config.folders.chapter
    scene_keys = config.scenes.keys()
    result_file = config.files.result

    stitch_videos(chapter_folder, scene_keys, result_file)

    print(f"✔ GENERATED CHAPTER {config.chapter} -> {config.files.result}")

def _finalize(config):

    copy_file(config.files.source, config.files.cache)
