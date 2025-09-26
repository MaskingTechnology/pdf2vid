
import ffmpeg

from utils.filesystem import join_paths

PLAYLIST_FILENAME = "playlist.txt"

def stitch_videos(input_folder, video_names, output_file):

    playlist_file = join_paths(input_folder, PLAYLIST_FILENAME)
    
    with open(playlist_file, "w") as file:
        for video_name in video_names:
            file.write(f"file '{video_name}.mp4'\n")

    (
        ffmpeg
        .input(playlist_file, format="concat", safe=0)
        .output(output_file, c="copy")
        .run(overwrite_output=True, quiet=True)
    )
