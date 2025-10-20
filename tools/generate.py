
import argparse

parser = argparse.ArgumentParser(description="Generates a scene from configuration.")

parser.add_argument("--config", type=str, required=True, help="The video configuration.")
parser.add_argument("--output", type=str, required=True, help="The video output folder.")
parser.add_argument("--chapter", type=str, required=False, help="If set, only the chapter with this id is generated.")
parser.add_argument("--scene", type=str, required=False, help="If set, only the scene with this id is generated.")

args = parser.parse_args()

from .flows.video import generate_video

try:
    generate_video(args.config, args.output, args.chapter, args.scene)
except RuntimeError as error:
    print(f"✘ {error}")
