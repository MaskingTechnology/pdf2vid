
import hashlib
import os

from .filesystem import read_file, write_file

CHUNK_SIZE = 4096

def read_file_hash(hash_path):

    return read_file(hash_path)

def write_file_hash(file_path, hash_path):

    file_hash = _generate_file_hash(file_path)

    write_file(hash_path, file_hash)

def file_hash_changed(file_path, hash_path):

    generated_hash = _generate_file_hash(file_path)
    read_hash = read_file_hash(hash_path)

    return generated_hash != read_hash

def _generate_file_hash(file_path):

    md5_hash = hashlib.md5()

    with open(file_path, "rb") as file:
        
        chunk = file.read(CHUNK_SIZE)
        
        while chunk:

            md5_hash.update(chunk)

            chunk = file.read(CHUNK_SIZE)

    return md5_hash.hexdigest()
