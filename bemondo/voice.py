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


AUDIO_EXTS = (".wav", ".mp3", ".m4a", ".flac", ".ogg", ".aac", ".wma")
MAX_REF_SEC = 12.0


def find_ref_audio(voice_dir: Path) -> Path | None:
    """ref.wav, vagy bármilyen ref.<hangformátum> a mappában."""
    for ext in AUDIO_EXTS:
        p = voice_dir / f"ref{ext}"
        if p.exists():
            return p
    return None


def ensure_ref_wav(voice_dir: Path) -> Path:
    """Ha nincs ref.wav, de van pl. ref.mp3, átalakítja (vágás nélkül, hogy a ref.txt továbbra is igaz maradjon).
    12 s-nál hosszabb felvételt nem fogad el: ahhoz a `bemondo hang` parancs kell, ami vág és átiratot készít."""
    wav = voice_dir / "ref.wav"
    if wav.exists():
        return wav
    src = find_ref_audio(voice_dir)
    if src is None:
        raise FileNotFoundError(f"Nincs referencia-hang a {voice_dir} mappában (ref.wav vagy ref.mp3).")
    audio = _load_mono(src)
    if len(audio) / 1000 > MAX_REF_SEC:
        raise ValueError(
            f"{src.name} {len(audio) / 1000:.1f} s hosszú, a megengedett legfeljebb {MAX_REF_SEC:.0f} s. "
            f"Készíts belőle referenciát: bemondo hang \"{src}\" --nev {voice_dir.name}"
        )
    audio = audio.apply_gain(-20.0 - audio.dBFS)
    if len(silence.detect_silence(audio[-TAIL_SILENCE_MS:], min_silence_len=TAIL_SILENCE_MS, silence_thresh=audio.dBFS - 16)) == 0:
        audio += AudioSegment.silent(TAIL_SILENCE_MS, frame_rate=SAMPLE_RATE)
    audio.export(wav, format="wav")
    print(f"{src.name} -> ref.wav ({len(audio) / 1000:.1f} s)")
    return wav


def _load_mono(src: Path) -> AudioSegment:
    # ffmpeg-gel WAV-vá alakítunk, így a pydub-nak nem kell ffprobe
    wav = subprocess.run(
        [ffmpeg_exe(), "-v", "error", "-i", str(src), "-ac", "1", "-ar", str(SAMPLE_RATE), "-f", "wav", "-"],
        check=True, capture_output=True,
    ).stdout
    return AudioSegment.from_wav(io.BytesIO(wav))


def prepare_reference(src: Path, dest_dir: Path, max_sec: float = 10.0, min_sec: float = 5.0, cut_sec: float | None = None) -> Path:
    """cut_sec: ha adott (pl. Whisper szerinti mondatvég), ott vágunk; különben csendnél."""
    audio = _load_mono(src)

    if cut_sec is not None:
        start, end = 0, int(cut_sec * 1000)
        # kezdő csend levágása
        lead = silence.detect_leading_silence(audio, silence_threshold=audio.dBFS - 16)
        start = max(0, lead - 100)
        return _export(audio[start:end + 50], dest_dir)

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

    return _export(audio[max(0, start - 100):end + 50], dest_dir)


def _export(clip: AudioSegment, dest_dir: Path) -> Path:
    clip = clip.apply_gain(-20.0 - clip.dBFS)  # egységes hangerő
    clip += AudioSegment.silent(TAIL_SILENCE_MS, frame_rate=SAMPLE_RATE)
    dest_dir.mkdir(parents=True, exist_ok=True)
    out = dest_dir / "ref.wav"
    clip.export(out, format="wav")
    print(f"Referencia mentve: {out} ({len(clip) / 1000:.1f} s)")
    return out
