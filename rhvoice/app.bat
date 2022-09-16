@echo off
SETLOCAL
set RHVOICELIBPATH=C:\Program Files (x86)\RHVoice\lib64\RHVoice.dll
set RHVOICEDATAPATH=C:\Program Files (x86)\RHVoice\data

set LAMEPATH=C:\Program Files\lame\lame.exe
set OPUSENCPATH=C:\Program Files\opus-tools\opusenc.exe

set THREADED=1

@echo on
python.exe -u app.py
pause
