
from pathlib import Path
import shutil
import os

def get_parent_path(file_path):
    
    return Path(file_path).parent

def join_paths(*paths):

    return os.path.join(*paths)

def path_exists(path):

    return os.path.exists(path)

def create_folder(path):

    os.makedirs(path)

def remove_folder(folder_path):

    shutil.rmtree(folder_path, ignore_errors=True)

def read_file(file_path):

    if not path_exists(file_path):
        return None
    
    with open(file_path, "r") as file:
        return file.read()

def write_file(file_path, content):
    
    with open(file_path, "w") as file:
        file.write(content)

def copy_file(source_path, target_path):

    shutil.copy2(source_path, target_path)

def remove_file(file_path):

    Path(file_path).unlink(missing_ok=True)
