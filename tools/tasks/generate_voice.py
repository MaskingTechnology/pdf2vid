
from kokoro import KPipeline
import soundfile
import warnings

VOICE = 'af_heart'

warnings.filterwarnings("ignore")

def generate_voice(text, speed, output_file):

    pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
    generator = pipeline(text, VOICE, speed=speed)

    for index, (graphemes, phonemes, audio) in enumerate(generator):
        soundfile.write(output_file, audio, 24000)
