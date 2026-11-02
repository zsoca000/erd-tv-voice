# Bemondó – Hungarian announcer voice from text

Generates Hungarian announcement audio in a cloned voice. Built on [F5-TTS](https://github.com/SWivid/F5-TTS)
with [sarpba](https://huggingface.co/sarpba)'s Hungarian weights; both are downloaded automatically.

## Setup (Windows, NVIDIA GPU)

1. Install [Python 3.10–3.12](https://www.python.org/downloads/), tick **"Add python.exe to PATH"**.
2. Download this repo (**Code → Download ZIP**, unzip) or `git clone https://github.com/zsoca000/erd-tv-voice`.
3. Add the voice: copy the `ref.wav` and `ref.txt` you received into `voices/panna/`.
4. Run **`telepit.bat`** once (~10 min, downloads ~2 GB of models).

## Use

1. Run **`bemondo.bat`** – the UI opens in your browser.
2. Type the text, press **Bemondás**. Write numbers and times as digits (`19:30`, `2025. március 15.`, `M1`, `2-es`).
3. Listen, download. Files also land in `output/`. Re-listen to sentences marked ⚠ in the table.

Update: download the new version, run `telepit.bat` again.

## Voices

A voice is a folder `voices/<name>/` with two files (not committed – they are private):

- `ref.wav` (or `ref.mp3` / `ref.m4a` / `ref.flac`) – 6–10 s of clean speech, **max 12 s**, no music
- `ref.txt` – exact transcript of the audio, word for word

A new folder shows up in the UI after pressing ↻ next to the voice list. If the recording is longer than 12 s,
make a reference from it: `bemondo hang recording.mp3 --nev <name>` – it cuts a ≤10 s segment and writes a
Whisper transcript; listen to the produced `ref.wav` and fix `ref.txt` by hand. Default voice: `voice:` in `config.yaml`.

## Developer

```bash
python -m venv .venv && .venv\Scripts\activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
pip install -e .

bemondo norm "A híradó 19:30-kor."   # show the spoken form
bemondo mond szoveg.txt -o out.wav   # generate from file or text
bemondo ui [--host 0.0.0.0]          # web UI (0.0.0.0 = reachable on LAN)
```

Flow: text → sentences → normalisation → F5-TTS per sentence → Whisper checks each sentence, retries with a new
seed if it differs → joined WAV + `.json` with all settings and seeds.

| Change | Where |
|---|---|
| Model, parameters, default voice | `config.yaml` (new weights: `model.ckpt: hf://user/repo/file`) |
| Pronunciation dictionary | `bemondo/normaliser/changes.csv` |
| Another TTS engine | new class in `bemondo/engine.py` with the same `synth()` |

Licence: Hungarian weights CC-BY-NC-4.0 (non-commercial), F5-TTS MIT.
