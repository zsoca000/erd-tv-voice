@echo off
chcp 65001 >nul
cd /d "%~dp0"
if not exist .venv\Scripts\activate.bat (
  echo Elobb futtasd a telepit.bat-ot.
  pause & exit /b 1
)
call .venv\Scripts\activate.bat
echo Bemondo indul, a bongeszoben megnyilik: http://127.0.0.1:7860
echo (Ezt az ablakot hagyd nyitva, amig dolgozol.)
bemondo ui
pause
