@echo off
chcp 65001 > nul
echo.
python3 banner.py
echo.
start cmd /k "python3 GoogleDomain.py -f domain.txt"
echo.
start cmd /k "python3 FireFoxDomain.py -f domain.txt"
echo.
pause > nul