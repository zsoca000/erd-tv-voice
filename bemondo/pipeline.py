"""A teljes bemondás-folyamat egy helyen; a parancssor és a felület is ezt hívja.

szöveg → mondatok → normalizálás → F5-TTS mondatonként → Whisper-ellenőrzés,
rossz mondat újra más seeddel → összefűzés szünetekkel → WAV + jelentés.
"""

import json
import time
from pathlib import Path

import numpy as np
import soundfile as sf
import yaml

from bemondo.engine import load_engine
from bemondo.text import group_sentences, normalize_text, split_sentences

ROOT = Path(__file__).resolve().parent.parent


def load_config(path: Path | None = None) -> dict:
    with open(path or ROOT / "config.yaml", encoding="utf-8") as f:
        return yaml.safe_load(f)


def list_voices() -> list[str]:
    vdir = ROOT / "voices"
    return sorted(p.name for p in vdir.iterdir() if (p / "ref.wav").exists() and (p / "ref.txt").exists())


class Bemondo:
    """A modelleket egyszer tölti be, utána akárhány bemondást generál."""

    def __init__(self, cfg: dict, qa: bool = True):
        self.cfg = cfg
        self.engine = load_engine(cfg["model"], ROOT)
        self.sr = self.engine.sample_rate
        self.transcriber = None
        if qa and cfg["qa"]["enabled"]:
            from bemondo.qa import Transcriber

            self.transcriber = Transcriber(cfg["qa"]["whisper_model"])

    def generate(self, text: str, voice: str, progress=None):
        """Visszaad: (wav float32, mintavételi ráta, mondatonkénti jelentés)."""
        from bemondo.qa import error_rate

        gen, qa_cfg = self.cfg["generation"], self.cfg["qa"]
        voice_dir = ROOT / "voices" / voice
        ref_wav = voice_dir / "ref.wav"
        ref_text = normalize_text((voice_dir / "ref.txt").read_text(encoding="utf-8").strip(), prefix=False)

        sentences = group_sentences(split_sentences(text), gen.get("chunk_chars", 0))
        pause = np.zeros(int(gen["pause_sec"] * self.sr), dtype=np.float32)
        pieces, report = [], []
        for i, sentence in enumerate(sentences, 1):
            if progress:
                progress(i - 1, len(sentences), sentence)
            target = normalize_text(sentence)
            best = None
            tries = qa_cfg["max_tries"] if self.transcriber else 1
            for t in range(tries):
                seed = gen["seed"] + i * 1000 + t
                wav = self.engine.synth(target, ref_wav, ref_text, seed, gen)
                if not self.transcriber:
                    best = {"wav": wav, "seed": seed, "tries": t + 1}
                    break
                heard = self.transcriber.transcribe(wav, self.sr)
                err = error_rate(sentence, heard)
                if best is None or err < best["error"]:
                    best = {"wav": wav, "seed": seed, "heard": heard, "error": err, "tries": t + 1}
                if err <= qa_cfg["max_error"]:
                    break
            best["ok"] = best.get("error", 0.0) <= qa_cfg["max_error"]
            pieces += [best["wav"], pause]
            report.append({k: v for k, v in best.items() if k != "wav"} | {"text": sentence, "normalized": target})
        if progress:
            progress(len(sentences), len(sentences), "")
        return np.concatenate(pieces[:-1]), self.sr, report

    def save(self, wav, report, voice: str, out: Path | None = None) -> Path:
        out = Path(out or ROOT / "output" / f"bemondas_{time.strftime('%Y%m%d_%H%M%S')}.wav")
        out.parent.mkdir(parents=True, exist_ok=True)
        sf.write(out, wav, self.sr)
        meta = {"config": self.cfg, "voice": voice, "sentences": report}
        out.with_suffix(".json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8")
        return out
