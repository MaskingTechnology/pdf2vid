
from kokoro import KPipeline
import soundfile
import warnings

VOICE = 'af_heart'
SAMPLE_RATE = 24000

warnings.filterwarnings("ignore")

def generate_voice(text, speed, delay, output_file):

    pipeline = KPipeline(lang_code='a', repo_id='hexgrad/Kokoro-82M')
    generator = pipeline(text, VOICE, speed=speed)

    for index, (graphemes, phonemes, audio) in enumerate(generator):
        
        if (delay > 0):
            audio = _add_delay(audio, delay)
        
        soundfile.write(output_file, audio, SAMPLE_RATE)

def _add_delay(audio, duration):

    import torch

    samples = int(duration * SAMPLE_RATE)
  
    delay = torch.zeros((samples,), dtype=audio.dtype, device=audio.device)

    return torch.cat((delay, audio), dim=0)