"""Minőségellenőrzés: a generált mondatot Whisperrel visszaírjuk és összevetjük a célszöveggel.
A betoldott vagy elnyelt szótagok így mérhető hibaként jelennek meg."""

import difflib

import numpy as np
import soundfile as sf

from bemondo.text import compare_key


class Transcriber:
    def __init__(self, model_name: str):
        from faster_whisper import WhisperModel

        self.model = WhisperModel(model_name, device="auto", compute_type="default")

    def transcribe(self, audio, sample_rate: int = 16000) -> str:
        """audio: fájlútvonal vagy float32 tömb (ekkor sample_rate szerint 16 kHz-re hozzuk)."""
        if not isinstance(audio, np.ndarray):  # soundfile-lal olvasunk, hogy ne kelljen az av csomag
            audio, sample_rate = sf.read(str(audio), dtype="float32")
            if audio.ndim > 1:
                audio = audio.mean(axis=1)
        if sample_rate != 16000:
            idx = np.linspace(0, len(audio) - 1, int(len(audio) * 16000 / sample_rate))
            audio = np.interp(idx, np.arange(len(audio)), audio).astype(np.float32)
        segments, _ = self.model.transcribe(audio, language="hu", beam_size=5, vad_filter=False)
        return " ".join(s.text.strip() for s in segments)


def error_rate(target: str, heard: str) -> float:
    """Karakterszintű eltérés aránya (0 = tökéletes)."""
    a, b = compare_key(target), compare_key(heard)
    if not a:
        return 0.0 if not b else 1.0
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    errors = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in matcher.get_opcodes() if op != "equal")
    return errors / len(a)
