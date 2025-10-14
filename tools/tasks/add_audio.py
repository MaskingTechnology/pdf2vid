
import ffmpeg

def add_audio(video_file, audio_file, output_file):

    video_input = ffmpeg.input(video_file)
    audio_input = ffmpeg.input(audio_file)

    (
        ffmpeg
        .output(video_input, audio_input, output_file)
        .run(overwrite_output=True, quiet=True)
    )
