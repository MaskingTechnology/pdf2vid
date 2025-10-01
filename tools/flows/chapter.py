
from tasks.stitch_videos import stitch_videos

from models.chapter import FolderPaths, FilePaths, Config

from utils.config import read_config
from utils.filesystem import join_paths

### DEFAULTS ##########################

CHAPTER_DEFAULT = "C1"
DESCRIPTION_DEFAULT = ""
SCENES_DEFAULT = []

### PROCESS ##########################

def generate_chapter(config_file, output_folder):

    config = _create_config(config_file, output_folder)

    _generate(config)

### CONFIG ##########################

def _create_config(config_file, output_folder):

    data = read_config(config_file)

    chapter = data.get("chapter", CHAPTER_DEFAULT)
    description = data.get("description", DESCRIPTION_DEFAULT)
    scenes = data.get("scenes", SCENES_DEFAULT)
    folders = _create_folder_paths(output_folder, chapter)
    files = _create_file_paths(chapter, folders)

    return Config(
        chapter = chapter,
        description = description,
        scenes = scenes,
        folders = folders,
        files = files
    )

def _create_folder_paths(output_folder, chapter):

    cache_folder = join_paths(output_folder, "chapters")
    chapter_folder = join_paths(cache_folder, chapter)

    return FolderPaths(
        cache = cache_folder,
        chapter = chapter_folder
    )

def _create_file_paths(chapter, folders):

    result_file = join_paths(folders.cache, f"{chapter}.mp4")

    return FilePaths(
        result = result_file
    )

### PROCESS ##########################

def _generate(config):

    print("GENERATING CHAPTER")

    stitch_videos(config.folders.chapter, config.scenes, config.files.result)

    print(f"✔ {config.files.result}")
