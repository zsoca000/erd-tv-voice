"""Referencia-hang előkészítése tetszőleges hangfájlból.

Az F5-TTS 12 másodpercnél levágja a referenciát; ha a hozzá tartozó szöveg a teljes
hangot írja le, a modell a "felesleges" szöveget is kimondja (ebből lesznek a random
szótagok). Ezért itt mi vágunk, csendnél, és a szöveget a vágott részhez írjuk.
"""

import io
import shutil
import subprocess
from pathlib import Path

from pydub import AudioSegment, silence

SAMPLE_RATE = 24000
TAIL_SILENCE_MS = 500


def ffmpeg_exe() -> str:
    """Rendszerszintű ffmpeg, ha van; különben az imageio-ffmpeg csomagból (Windows-telepítő ezt teszi fel)."""
    if shutil.which("ffmpeg"):
        return "ffmpeg"
    import imageio_ffmpeg

    return imageio_ffmpeg.get_ffmpeg_exe()


def prepare_reference(src: Path, dest_dir: Path, max_sec: float = 10.0, min_sec: float = 5.0) -> Path:
    # ffmpeg-gel WAV-vá alakítunk, így a pydub-nak nem kell ffprobe
    wav = subprocess.run(
        [ffmpeg_exe(), "-v", "error", "-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "wav", "-"],
        check=True, capture_output=True,
    ).stdout
    audio = AudioSegment.from_wav(io.BytesIO(wav))

    # Beszédszakaszok csendek mentén; addig gyűjtünk, amíg beférünk max_sec-be.
    ranges = silence.detect_nonsilent(audio, min_silence_len=250, silence_thresh=audio.dBFS - 16, seek_step=10)
    if not ranges:
        raise ValueError("Nem található beszéd a hangfájlban.")
    start, end = ranges[0][0], ranges[0][1]
    for s, e in ranges[1:]:
        if (e - start) / 1000 > max_sec:
            break
        end = e
    if (end - start) / 1000 < min_sec:
        print(f"Figyelem: a referencia csak {(end - start) / 1000:.1f} s; 6–10 s az ideális.")
    if (end - start) / 1000 > max_sec:  # egyetlen hosszú szakasz, nincs csend benne
        end = start + int(max_sec * 1000)

    clip = audio[max(0, start - 100):end + 50]
    clip = clip.apply_gain(-20.0 - clip.dBFS)  # egységes hangerő
    clip += AudioSegment.silent(TAIL_SILENCE_MS, frame_rate=SAMPLE_RATE)

    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / "ref.wav"
    clip.export(out, format="wav")
    print(f"Referencia mentve: {out} ({len(clip) / 1000:.1f} s)")
    return out
