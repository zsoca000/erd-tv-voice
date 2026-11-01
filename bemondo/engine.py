"""Vékony réteg a TTS-motor fölött. Csak az F5-TTS nyilvános API-ját használja,
így az F5-TTS frissíthető (pip install -U f5-tts) anélkül, hogy ez a kód változna.
Másik motorhoz elég egy új osztály ugyanazzal a synth() metódussal.
"""

from pathlib import Path

import numpy as np


def resolve_path(ref: str, root: Path) -> str:
    """Helyi útvonal vagy hf://<felhasználó>/<repo>/<fájl> (letölti és gyorsítótárazza)."""
    if ref.startswith("hf://"):
        from huggingface_hub import hf_hub_download

        user, repo, filename = ref[5:].split("/", 2)
        return hf_hub_download(repo_id=f"{user}/{repo}", filename=filename)
    path = Path(ref)
    return str(path if path.is_absolute() else root / path)


class F5Engine:
    def __init__(self, model_cfg: dict, root: Path):
        from f5_tts.api import F5TTS

        device = model_cfg.get("device", "auto")
        self.tts = F5TTS(
            model=model_cfg["arch"],
            ckpt_file=resolve_path(model_cfg["ckpt"], root),
            vocab_file=resolve_path(model_cfg["vocab"], root),
            device=None if device == "auto" else device,
        )
        self.sample_rate = self.tts.target_sample_rate

    def synth(self, text: str, ref_wav: Path, ref_text: str, seed: int, gen: dict) -> np.ndarray:
        wav, _, _ = self.tts.infer(
            ref_file=str(ref_wav),
            ref_text=ref_text,
            gen_text=text,
            nfe_step=gen["nfe_step"],
            cfg_strength=gen["cfg_strength"],
            sway_sampling_coef=gen["sway_sampling_coef"],
            speed=gen["speed"],
            seed=seed,
            show_info=lambda *a, **k: None,
        )
        return np.asarray(wav, dtype=np.float32)


ENGINES = {"f5": F5Engine}


def load_engine(model_cfg: dict, root: Path):
    return ENGINES[model_cfg["engine"]](model_cfg, root)
