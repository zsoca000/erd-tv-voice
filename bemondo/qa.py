"""Minőségellenőrzés: a generált mondatot Whisperrel visszaírjuk és összevetjük a célszöveggel.
A betoldott vagy elnyelt szótagok így mérhető hibaként jelennek meg."""

import difflib

import numpy as np
import soundfile as sf

from bemondo.text import compare_key


def _add_torch_dlls():
    """Windows: a CTranslate2 (faster-whisper) a cuBLAS/cuDNN DLL-eket a PATH-on keresi; a PyTorch csomag
    hozza őket, csak a saját mappájában. Ezt vesszük fel a DLL-keresési útba."""
    import os
    import sys

    if sys.platform != "win32":
        return
    try:
        import torch

        lib = os.path.join(os.path.dirname(torch.__file__), "lib")
        if os.path.isdir(lib):
            os.add_dll_directory(lib)
            os.environ["PATH"] = lib + os.pathsep + os.environ.get("PATH", "")
    except Exception:
        pass


class Transcriber:
    def __init__(self, model_name: str):
        _add_torch_dlls()
        from faster_whisper import WhisperModel

        self.model = WhisperModel(model_name, device="auto", compute_type="default")
        # A GPU-s út csak az első futtatásnál derül ki (lazy); itt próbáljuk ki, és ha nem megy, CPU-ra váltunk.
        try:
            list(self.model.transcribe(np.zeros(16000, dtype=np.float32), language="hu", beam_size=1)[0])
        except RuntimeError as e:
            if "cublas" in str(e).lower() or "cudnn" in str(e).lower() or "cuda" in str(e).lower():
                print(f"Figyelem: a Whisper nem tud GPU-n futni ({e}); CPU-n folytatom, lassabb lesz.")
                self.model = WhisperModel(model_name, device="cpu", compute_type="int8")
            else:
                raise

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

    def words_with_times(self, path) -> list[tuple[float, float, str]]:
        """Szavak (kezdet, vég, szó) másodpercben, írásjelekkel együtt; a referencia vágásához."""
        audio, sr = sf.read(str(path), dtype="float32")
        if audio.ndim > 1:
            audio = audio.mean(axis=1)
        segments, _ = self.model.transcribe(audio if sr == 16000 else self._to16k(audio, sr), language="hu", beam_size=5, word_timestamps=True)
        return [(w.start, w.end, w.word) for seg in segments for w in (seg.words or [])]

    @staticmethod
    def _to16k(audio, sr):
        idx = np.linspace(0, len(audio) - 1, int(len(audio) * 16000 / sr))
        return np.interp(idx, np.arange(len(audio)), audio).astype(np.float32)


def error_rate(target: str, heard: str) -> float:
    """Karakterszintű eltérés aránya (0 = tökéletes)."""
    a, b = compare_key(target), compare_key(heard)
    if not a:
        return 0.0 if not b else 1.0
    matcher = difflib.SequenceMatcher(None, a, b, autojunk=False)
    errors = sum(max(i2 - i1, j2 - j1) for op, i1, i2, j1, j2 in matcher.get_opcodes() if op != "equal")
    return errors / len(a)
