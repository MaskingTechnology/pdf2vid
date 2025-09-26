
import argparse

from flows.scene import generate_scene
from flows.chapter import generate_chapter
from flows.video import generate_video

parser = argparse.ArgumentParser(description="Generates a scene from configuration.")

parser.add_argument("--type", type=str, required=True, help="The type to generate (scene, chapter or video).")
parser.add_argument("--config", type=str, required=True, help="The configuration.")
parser.add_argument("--output", type=str, required=True, help="The output folder.")

args = parser.parse_args()

match args.type.lower():

    case "scene":
        generate_scene(args.config, args.output)

    case "chapter":
        generate_chapter(args.config, args.output)
    
    case "video":
        generate_video(args.config, args.output)
    
    case _:
        print(f"Unknown type '{args.type}'")
