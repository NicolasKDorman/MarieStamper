@echo off
rem Builds dist\STAMPER.exe (needs Python on PATH)
python -m venv .venv || exit /b 1
.venv\Scripts\python.exe -m pip install -r requirements.txt || exit /b 1
.venv\Scripts\python.exe src\make_icon.py "%CD%\src\stamper.ico" || exit /b 1
.venv\Scripts\python.exe -m PyInstaller --noconfirm --onefile --windowed --name STAMPER --icon "%CD%\src\stamper.ico" --add-data "%CD%\src\stamper.ico;." --distpath dist --workpath build src\stamper.py
