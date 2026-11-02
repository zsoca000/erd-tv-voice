"""Parancssor.

  bemondo hang  <hangfájl> --nev panna     referencia előkészítése voices/panna/ alá
  bemondo mond  <szoveg.txt> -o ki.wav     bemondás generálása
  bemondo norm  "szöveg"                   csak a normalizálás eredményét mutatja
  bemondo ui                               egyszerűsített webes felület
"""

import argparse
import sys
from pathlib import Path

from bemondo.pipeline import ROOT, Bemondo, load_config


def cmd_hang(args, cfg):
    from bemondo.qa import Transcriber
    from bemondo.voice import prepare_reference

    import tempfile

    from bemondo.voice import _load_mono

    dest = ROOT / "voices" / args.nev
    src = Path(args.hangfajl)
    transcriber = Transcriber(cfg["qa"]["whisper_model"])

    # 1. A teljes felvétel mondatai időbélyeggel, hogy mondatvégnél vágjunk
    with tempfile.TemporaryDirectory() as tmp:
        full = Path(tmp) / "full.wav"
        _load_mono(src).export(full, format="wav")
        sentences = transcriber.sentences_with_times(full)
    fitting = [s for s in sentences if s[1] <= args.max]
    if fitting:
        cut = fitting[-1][1]
        text = " ".join(s[2] for s in fitting)
        print(f"Vágás az utolsó mondatvégnél: {cut:.1f} s ({len(fitting)} mondat)")
        ref = prepare_reference(src, dest, max_sec=args.max, cut_sec=cut)
    else:
        print(f"Figyelem: az első mondat is hosszabb {args.max:.0f} s-nál, csendnél vágok.")
        ref = prepare_reference(src, dest, max_sec=args.max)
        text = transcriber.transcribe(str(ref))

    (dest / "ref.txt").write_text(text + "\n", encoding="utf-8")
    print(f"Átirat: {text}")
    print(f"FONTOS: hallgasd meg a {ref} fájlt, és javítsd a {dest / 'ref.txt'} szövegét szóról szóra.")


def cmd_norm(args, cfg):
    from bemondo.text import normalize_text, split_sentences

    for s in split_sentences(args.szoveg):
        print(normalize_text(s))


def cmd_mond(args, cfg):
    src = Path(args.szoveg)
    text = src.read_text(encoding="utf-8") if src.exists() else args.szoveg
    voice = args.hang or cfg["voice"]

    bem = Bemondo(cfg, qa=not args.no_qa)
    wav, _, report = bem.generate(text, voice)
    for i, r in enumerate(report, 1):
        if "error" in r:
            flag = "OK" if r["ok"] else "ELLENŐRIZD!"
            print(f"[{i}/{len(report)}] hiba {r['error']:.0%}  {flag}  {r['text']}")
        else:
            print(f"[{i}/{len(report)}] {r['text']}")
    out = bem.save(wav, report, voice, Path(args.out) if args.out else None)
    print(f"Kész: {out}")


def cmd_ui(args, cfg):
    from bemondo.ui import build

    build(cfg).launch(server_name=args.host, server_port=args.port, inbrowser=not args.no_browser)


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Windows-konzolon is jók legyenek az ékezetek
    p = argparse.ArgumentParser(prog="bemondo")
    p.add_argument("--config")
    sub = p.add_subparsers(dest="cmd", required=True)

    h = sub.add_parser("hang", help="referencia-hang előkészítése")
    h.add_argument("hangfajl")
    h.add_argument("--nev", required=True)
    h.add_argument("--max", type=float, default=10.0, help="max hossz másodpercben")

    m = sub.add_parser("mond", help="bemondás generálása")
    m.add_argument("szoveg", help="szövegfájl vagy közvetlenül a szöveg")
    m.add_argument("-o", "--out")
    m.add_argument("--hang", help="a config.yaml-beli hang felülírása")
    m.add_argument("--no-qa", action="store_true", help="Whisper-ellenőrzés kihagyása")

    n = sub.add_parser("norm", help="normalizálás kipróbálása")
    n.add_argument("szoveg")

    u = sub.add_parser("ui", help="webes felület")
    u.add_argument("--host", default="127.0.0.1", help="0.0.0.0 = hálózatról is elérhető")
    u.add_argument("--port", type=int, default=7860)
    u.add_argument("--no-browser", action="store_true")

    args = p.parse_args()
    cfg = load_config(Path(args.config) if args.config else None)
    {"hang": cmd_hang, "mond": cmd_mond, "norm": cmd_norm, "ui": cmd_ui}[args.cmd](args, cfg)


if __name__ == "__main__":
    main()
