@echo off
chcp 65001 > nul
echo.
python3 FireFoxDomain.py -f domain.txt
echo.
pause