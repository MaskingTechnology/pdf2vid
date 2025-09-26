
from tasks.stitch_videos import stitch_videos

from models.video import FolderPaths, FilePaths, Config

from utils.config import read_config
from utils.filesystem import join_paths

### DEFAULTS ##########################

VIDEO_DEFAULT = "Video"
DESCRIPTION_DEFAULT = ""
CHAPTERS_DEFAULT = []

### PROCESS ##########################

def generate_video(config_file, output_folder):

    config = _create_config(config_file, output_folder)

    _generate(config)

### CONFIG ##########################

def _create_config(config_file, output_folder):

    data = read_config(config_file)

    video = data.get("video", VIDEO_DEFAULT)
    description = data.get("description", DESCRIPTION_DEFAULT)
    chapters = data.get("chapters", CHAPTERS_DEFAULT)
    folders = _create_folder_paths(output_folder)
    files = _create_file_paths(video, folders)

    return Config(
        video = video,
        description = description,
        chapters = chapters,
        folders = folders,
        files = files
    )

def _create_folder_paths(output_folder):

    cache_folder = join_paths(output_folder, "cache")

    return FolderPaths(
        output = output_folder,
        cache = cache_folder
    )

def _create_file_paths(video, folders):

    result_file = join_paths(folders.output, f"{video}.mp4")

    return FilePaths(
        result = result_file
    )

### PROCESS ##########################

def _generate(config):

    print("GENERATING VIDEO")

    stitch_videos(config.folders.cache, config.chapters, config.files.result)

    print(f"✔ {config.files.result}")
