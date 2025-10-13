
import ffmpeg

from utils.filesystem import join_paths

def stitch_videos(input_folder, video_names, output_file):

    inputs = []

    for video_name in video_names:
        full_path = join_paths(input_folder, f"{video_name}.mp4")
        inputs.append(ffmpeg.input(full_path))

    video_streams = [entry.video for entry in inputs]
    audio_streams = [entry.audio for entry in inputs]

    stream_pairs = []

    for inp in inputs:
        stream_pairs.extend([inp.video, inp.audio])

    joined = ffmpeg.concat(*stream_pairs, v=1, a=1)
    joined = joined.filter('setpts', 'PTS-STARTPTS')

    joined.output(
        output_file,
        vcodec='libx264',
        acodec='aac',
        strict='experimental',
        movflags='+faststart'
    ).run(overwrite_output=True, quiet=True)
