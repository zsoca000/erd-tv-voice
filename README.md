# Bemondó – magyar bemondószöveg saját hangon

Vékony réteg az [F5-TTS](https://github.com/SWivid/F5-TTS) fölött, [sarpba](https://huggingface.co/sarpba) magyar
modellsúlyaival. A keretrendszer PyPI-ról, a súlyok Hugging Face-ről jönnek automatikusan; ez a repo csak a saját
kódot, a kiejtési szótárat és a hangokat tartalmazza.

## Szerkesztőnek: telepítés és használat (Windows, NVIDIA kártyával)

1. [Python 3.10–3.12](https://www.python.org/downloads/) telepítése, az **„Add python.exe to PATH”** pipával.
2. A repo letöltése (zöld **Code → Download ZIP**, kicsomagolás), vagy `git clone`.
3. Dupla katt: **`telepit.bat`** – egyszer kell, ~10 perc, letölti a modelleket (~2 GB).
4. Dupla katt: **`bemondo.bat`** – megnyílik a böngészőben a felület.
5. Szöveg beírása, hang kiválasztása, **Bemondás**. A kész WAV az `output/` mappába kerül, a felületről letölthető.

Számokat, időpontokat, dátumokat írj nyugodtan számmal: `19:30`, `2025. március 15.`, `M1`, `2-es`, `kb.`.
A táblázatban a ⚠ jelű mondatokat hallgasd vissza: ott a gép visszahallott szövege eltért a beírttól.

**Frissítés:** új repo-verzió letöltése után ismét `telepit.bat`.

## Fejlesztőnek

```bash
python -m venv .venv && .venv\Scripts\activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -e . imageio-ffmpeg

bemondo hang PANNA_HANG.mp3 --nev panna   # referencia: 6–10 s-os részlet + Whisper-átirat → voices/panna/
                                          # utána: hallgasd meg a ref.wav-ot, javítsd a ref.txt-t szóról szóra!
bemondo norm "A híradó 19:30-kor az M1-en." # normalizálás kipróbálása
bemondo mond szoveg.txt -o output/hirado.wav
bemondo ui [--host 0.0.0.0]               # felület; 0.0.0.0-val hálózatról is elérhető
```

### Hogyan működik

```
szöveg → mondatokra bontás → normalizálás (számok, rövidítések, kiejtési szótár)
      → F5-TTS mondatonként (referencia-hang + szöveg, rögzített seed)
      → Whisper visszahallgatja; ha eltér, új seeddel újra (max_tries), a legjobbat tartja
      → összefűzés szünetekkel → WAV + .json (minden beállítás és seed, reprodukálható)
```

A referenciát mi vágjuk 10 s alá, csendnél, záró csenddel; ezért nem kell az F5-TTS-nek vágnia, és a
referenciaszöveg a hanghoz tartozik. (Ennek hiánya okozta a korábbi „random szótag” hibát.)

### Hol mit állíts

| Mit | Hol |
|---|---|
| Modell, paraméterek, alap-hang, ellenőrzés szigorúsága | `config.yaml` |
| Kiejtési szótár (rövidítések, idegen szavak) | `bemondo/normaliser/changes.csv` (`kulcs, kiejtés`) |
| Hangok | `voices/<név>/ref.wav` + `ref.txt` |

### Frissítés

- **F5-TTS:** `pyproject.toml`-ban a rögzített verzió emelése, tesztelés, commit.
- **Új magyar modell:** `config.yaml` → `model.ckpt` / `model.vocab`, pl. `hf://sarpba/F5-TTS_V1_hun_2509/model_302000.with_EMA.safetensors`.
- **Másik motor (pl. VibeVoice):** új osztály a `bemondo/engine.py`-ban ugyanazzal a `synth()` metódussal, majd `model.engine` a configban.

### Felépítés

```
bemondo/
  pipeline.py   a teljes folyamat (CLI és UI is ezt hívja)
  text.py       mondatbontás, normalizálás hívása
  normaliser/   magyar normalizáló (sarpba F5-TTS_hun-ból átvéve) + suffix.py (2-es, 12-kor, 100-an)
  voice.py      referencia vágása, hangerő, záró csend
  engine.py     F5-TTS nyilvános API (f5_tts.api.F5TTS); hf:// letöltés
  qa.py         Whisper-visszaellenőrzés, hibaarány
  ui.py         egyszerűsített Gradio felület
  cli.py        parancsok
```

Licenc: a magyar modellsúlyok CC-BY-NC-4.0 (nem kereskedelmi); az F5-TTS MIT.
