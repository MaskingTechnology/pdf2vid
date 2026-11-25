
from kokoro import KPipeline
import soundfile
import warnings

VOICE = "af_heart"
SAMPLE_RATE = 24000

warnings.filterwarnings("ignore")

def generate_voice(text, speed, delay, output_file):

    pipeline = KPipeline(lang_code="a", repo_id="hexgrad/Kokoro-82M")
    generator = pipeline(text, VOICE, speed=speed)

    audios = []

    for graphemes, phonemes, audio in generator:

        audios.append(audio)

    if not audios:
        return

    import torch

    full_audio = torch.cat(audios, dim=0)

    if delay > 0:
        full_audio = _add_delay(full_audio, delay)

    soundfile.write(output_file, full_audio, SAMPLE_RATE)

def _add_delay(audio, duration):

    import torch

    samples = int(duration * SAMPLE_RATE)

    delay = torch.zeros((samples,), dtype=audio.dtype, device=audio.device)

    return torch.cat((delay, audio), dim=0)
