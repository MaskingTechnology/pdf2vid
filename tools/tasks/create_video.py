
import argparse
import ffmpeg

DEFAULT_FRAMERATE = 10

def create_video(input_folder, output_file, framerate = DEFAULT_FRAMERATE):

    input_pattern = f"{input_folder}/%03d.png"

    (
        ffmpeg
        .input(input_pattern, r=framerate)
        .output(output_file, vcodec='libx264', pix_fmt='yuv420p')
        .run(overwrite_output=True, quiet=True)
    )
