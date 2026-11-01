@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo === Bemondo telepites ===

where python >nul 2>nul || (
  echo HIBA: Python nem talalhato. Telepitsd a python.org-rol (3.10-3.12), es pipald be az "Add to PATH" opciot.
  pause & exit /b 1
)

if not exist .venv (
  echo Virtualis kornyezet letrehozasa...
  python -m venv .venv || (echo HIBA: venv nem sikerult & pause & exit /b 1)
)
call .venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip

where nvidia-smi >nul 2>nul
if %errorlevel%==0 (
  echo NVIDIA kartya talalva, GPU-s PyTorch telepitese...
  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
) else (
  echo Nincs NVIDIA kartya, CPU-s PyTorch telepitese (lassu lesz!)...
  pip install torch torchaudio
)
if errorlevel 1 (echo HIBA: PyTorch telepites nem sikerult & pause & exit /b 1)

echo Bemondo es fuggosegek telepitese/frissitese...
pip install --upgrade -e . imageio-ffmpeg || (echo HIBA: telepites nem sikerult & pause & exit /b 1)

echo Modellek letoltese (elso alkalommal ~2 GB)...
python -c "from pathlib import Path; from bemondo.pipeline import load_config, ROOT; from bemondo.engine import resolve_path; c=load_config()['model']; resolve_path(c['ckpt'], ROOT); resolve_path(c['vocab'], ROOT); print('Modell OK')"
python -c "from bemondo.pipeline import load_config; from faster_whisper import WhisperModel; WhisperModel(load_config()['qa']['whisper_model']); print('Whisper OK')"

echo.
echo === Kesz. Inditas: bemondo.bat ===
pause
