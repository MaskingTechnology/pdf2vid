
import json
import os

def read_config(config_file):

    if not os.path.exists(config_file):
        return None

    try:
        with open(config_file, "r") as file:
            return json.load(file)
    except json.JSONDecodeError:
        raise RuntimeError(f"Invalid JSON in configuration {config_file}!")
