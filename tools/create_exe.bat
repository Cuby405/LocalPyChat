@echo off

REM CLIENTE
python -m PyInstaller --onefile --windowed --icon=tools/icon.ico ^
--add-data "tools/updater.py;." ^
--add-data "tools/version.txt;." ^
client.py

REM SERVIDOR
python -m PyInstaller --onefile --windowed --icon=tools/icon.ico server.py

pause
