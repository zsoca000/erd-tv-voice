@echo off
chcp 65001 >nul
setlocal
cd /d "%~dp0"
echo === Bemondo telepites ===
echo.

where python >nul 2>nul
if errorlevel 1 (
  echo HIBA: Python nem talalhato.
  echo Telepitsd a python.org-rol, 3.10 - 3.12 kozotti verziot, es pipald be az "Add python.exe to PATH" opciot.
  goto :hiba
)

if not exist .venv (
  echo Virtualis kornyezet letrehozasa...
  python -m venv .venv
  if errorlevel 1 (
    echo HIBA: a virtualis kornyezet letrehozasa nem sikerult.
    goto :hiba
  )
)
call .venv\Scripts\activate.bat
python -m pip install --quiet --upgrade pip

where nvidia-smi >nul 2>nul
if errorlevel 1 (
  echo Nincs NVIDIA kartya: CPU-s PyTorch telepitese. Lassu lesz!
  pip install torch torchaudio
  if errorlevel 1 goto :torch_hiba
) else (
  echo NVIDIA kartya talalva: GPU-s PyTorch telepitese...
  pip install torch torchaudio --index-url https://download.pytorch.org/whl/cu124
  if errorlevel 1 goto :torch_hiba
)

echo Bemondo es fuggosegek telepitese / frissitese...
pip install --upgrade -e .
if errorlevel 1 (
  echo HIBA: a bemondo telepitese nem sikerult.
  goto :hiba
)

echo Modellek letoltese, elso alkalommal kb. 2 GB...
python -c "from bemondo.pipeline import load_config, ROOT; from bemondo.engine import resolve_path; c=load_config()['model']; resolve_path(c['ckpt'], ROOT); resolve_path(c['vocab'], ROOT); print('Modell OK')"
if errorlevel 1 (
  echo HIBA: a modell letoltese nem sikerult.
  goto :hiba
)
python -c "from bemondo.pipeline import load_config; from faster_whisper import WhisperModel; WhisperModel(load_config()['qa']['whisper_model']); print('Whisper OK')"
if errorlevel 1 (
  echo HIBA: a Whisper modell letoltese nem sikerult.
  goto :hiba
)

echo.
echo === Kesz. Inditas: bemondo.bat ===
pause
exit /b 0

:torch_hiba
echo HIBA: a PyTorch telepitese nem sikerult.

:hiba
echo.
echo A telepites megszakadt. A fenti hibauzenetet kuldd el a projekt gazdajanak.
pause
exit /b 1
