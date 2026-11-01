# Bemondó – Hungarian TV announcer voice (voice-cloned TTS)

Generates Hungarian announcement audio in a given person's voice from plain text.
A thin layer on top of [F5-TTS](https://github.com/SWivid/F5-TTS) with [sarpba](https://huggingface.co/sarpba)'s
Hungarian fine-tuned weights. The framework comes from PyPI and the weights from Hugging Face automatically;
this repo only holds our own code, the pronunciation dictionary and the config.

## Quick start (Windows, NVIDIA GPU)

1. Install [Python 3.10–3.12](https://www.python.org/downloads/) and tick **"Add python.exe to PATH"**.
2. Get this repo: green **Code → Download ZIP** and unzip, or `git clone https://github.com/zsoca000/erd-tv-voice`.
3. **Add a voice** (see below): put `ref.wav` and `ref.txt` into `voices/<name>/`. You get these files from the
   project owner, or create them yourself.
4. Double-click **`telepit.bat`** – one-time setup, ~10 min, downloads the models (~2 GB).
5. Double-click **`bemondo.bat`** – the UI opens in your browser.
6. Type the text, pick the voice, press **Bemondás**. The WAV lands in `output/` and can be downloaded from the UI.

Write numbers, times and dates as digits: `19:30`, `2025. március 15.`, `M1`, `2-es`, `kb.` – they are expanded
to spoken Hungarian automatically. In the result table, re-listen to sentences marked ⚠: there the machine
heard something different from what you typed.

**Update:** download the new version of the repo and run `telepit.bat` again.

## Adding a voice

Voices live in `voices/<name>/` and are **not committed** (they are private; `voices/` is git-ignored).
Each voice is two files:

| File | What |
|---|---|
| `voices/<name>/ref.wav` | 6–10 s of clean speech, mono, no music, ~0.5 s of silence at the end |
| `voices/<name>/ref.txt` | the exact transcript of `ref.wav`, word for word, with punctuation |

**Option A – you already have the two files:** copy the folder into `voices/`. Done.

**Option B – make them from any recording** (a longer MP3/WAV of the person speaking):

```bash
.venv\Scripts\activate
bemondo hang recording.mp3 --nev panna
```

This cuts a ≤10 s segment at a natural pause, normalises the volume, adds trailing silence, and writes a Whisper
transcript to `voices/panna/ref.txt`. **Listen to `ref.wav` and correct `ref.txt` word for word** – a transcript
that doesn't match the audio is the main cause of stray syllables in the output.

Set the default voice in `config.yaml` (`voice: panna`).

## CLI

```bash
bemondo hang <audio> --nev <name>   # prepare a voice (see above)
bemondo norm "A híradó 19:30-kor."  # show how the text will be pronounced
bemondo mond szoveg.txt -o out.wav  # generate (file or literal text)
bemondo ui [--host 0.0.0.0]         # web UI; 0.0.0.0 makes it reachable on the LAN
```

## Developer setup

```bash
python -m venv .venv && .venv\Scripts\activate
pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124   # or plain `pip install torch` for CPU
pip install -e . imageio-ffmpeg
```

### How it works

```
text → sentence split → normalisation (numbers, abbreviations, pronunciation dictionary)
     → F5-TTS per sentence (reference voice + text, fixed seed)
     → Whisper transcribes the result; if it differs, retry with a new seed (max_tries), keep the best
     → concatenate with pauses → WAV + .json (all settings and seeds; fully reproducible)
```

We trim the reference ourselves (≤10 s, at a pause, trailing silence) so F5-TTS doesn't have to, and the
reference transcript matches the audio. Missing this was what caused random syllables before.

### Where to change what

| What | Where |
|---|---|
| Model, generation parameters, default voice, QA strictness | `config.yaml` |
| Pronunciation dictionary (abbreviations, foreign words) | `bemondo/normaliser/changes.csv` (`key, pronunciation`) |
| Voices | `voices/<name>/ref.wav` + `ref.txt` |

### Updating

- **F5-TTS:** bump the pinned version in `pyproject.toml`, test, commit.
- **New Hungarian weights:** `config.yaml` → `model.ckpt` / `model.vocab`,
  e.g. `hf://sarpba/F5-TTS_V1_hun_2509/model_302000.with_EMA.safetensors`.
- **Another engine (e.g. VibeVoice):** add a class in `bemondo/engine.py` with the same `synth()` method,
  select it via `model.engine` in the config.

### Layout

```
bemondo/
  pipeline.py   the whole flow (used by both CLI and UI)
  text.py       sentence split, normalisation entry point
  normaliser/   Hungarian normaliser (from sarpba/F5-TTS_hun) + suffix.py (2-es, 12-kor, 100-an)
  voice.py      reference trimming, loudness, trailing silence
  engine.py     F5-TTS public API (f5_tts.api.F5TTS); hf:// downloads
  qa.py         Whisper back-transcription, error rate
  ui.py         simplified Gradio UI
  cli.py        commands
telepit.bat     one-time install (Windows)
bemondo.bat     start the UI (Windows)
```

Licence: the Hungarian weights are CC-BY-NC-4.0 (non-commercial); F5-TTS is MIT.
