@echo off
title Web Pemantauan Karhutla Kubu Raya
cd /d "%~dp0Multi-Agent-System"
python -m pip install -q -r requirements.txt -r requirements-gee.txt
echo.
echo Halaman web akan terbuka di peramban. Biarkan jendela ini terbuka selama memakai halaman.
python web_pantau.py
pause
