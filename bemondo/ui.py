"""Egyszerűsített felület a szerkesztőnek: szöveg be, hang ki.

A beállítások a config.yaml-ban maradnak; a felületen csak az látszik, ami a napi munkához kell.
"""

import argparse
import threading

import gradio as gr

from bemondo.pipeline import Bemondo, list_voices, load_config

_engine = None
_lock = threading.Lock()


def get_engine(cfg):
    global _engine
    with _lock:
        if _engine is None:
            _engine = Bemondo(cfg)
    return _engine


def build(cfg):
    voices = list_voices()

    def run(text, voice, progress=gr.Progress()):
        text = (text or "").strip()
        if not text:
            raise gr.Error("Írj be szöveget.")
        progress(0, desc="Modell betöltése…")
        bem = get_engine(cfg)

        def cb(i, n, sentence):
            progress(i / max(n, 1), desc=f"{i}/{n} mondat" + (f": {sentence[:50]}…" if sentence else ""))

        wav, sr, report = bem.generate(text, voice, progress=cb)
        out = bem.save(wav, report, voice)
        rows = [["✔" if r["ok"] else "⚠ ellenőrizd", r["text"], r.get("heard", "–"), f"{r.get('error', 0):.0%}"] for r in report]
        bad = sum(not r["ok"] for r in report)
        status = f"Kész: {out.name}" + (f" — {bad} mondatot hallgass vissza" if bad else " — minden mondat rendben")
        return str(out), rows, status

    with gr.Blocks(title="Bemondó") as app:
        gr.Markdown("## Bemondó\nÍrd be a szöveget, válassz hangot, és nyomd meg a gombot. Számokat, időpontokat nyugodtan írj számmal (pl. 19:30, M1, 2025. március 15.).")
        with gr.Row():
            with gr.Column(scale=3):
                text = gr.Textbox(label="Szöveg", lines=8, placeholder="Jó estét kívánunk! Következik a híradó…")
            with gr.Column(scale=1):
                voice = gr.Dropdown(voices, value=cfg["voice"] if cfg["voice"] in voices else (voices[0] if voices else None), label="Hang")
                btn = gr.Button("Bemondás", variant="primary")
                status = gr.Markdown()
        audio = gr.Audio(label="Eredmény", type="filepath", interactive=False)
        table = gr.Dataframe(headers=["", "Mondat", "Amit a gép visszahallott", "Eltérés"], interactive=False, wrap=True, label="Ellenőrzés")
        btn.click(run, [text, voice], [audio, table, status])
    return app


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--config")
    p.add_argument("--host", default="127.0.0.1", help="0.0.0.0 = hálózatról is elérhető")
    p.add_argument("--port", type=int, default=7860)
    p.add_argument("--no-browser", action="store_true")
    args = p.parse_args()
    cfg = load_config(args.config)
    build(cfg).launch(server_name=args.host, server_port=args.port, inbrowser=not args.no_browser)


if __name__ == "__main__":
    main()
