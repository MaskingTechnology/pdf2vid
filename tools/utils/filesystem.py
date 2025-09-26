
from pathlib import Path
import shutil
import os

def join_paths(*paths):
    return os.path.join(*paths)

def path_exists(path):
    return os.path.exists(path)

def copy_file(source_path, target_path):
    shutil.copy2(source_path, target_path)

def remove_file(file_path):
    Path(file_path).unlink(missing_ok=True)

def create_folder(path):
    os.makedirs(path)

def remove_folder(folder_path):
    shutil.rmtree(folder_path, ignore_errors=True)
