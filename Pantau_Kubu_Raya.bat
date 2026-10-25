@echo off
title Pemantauan Deforestasi dan Kebakaran - Kabupaten Kubu Raya
cd /d "%~dp0Multi-Agent-System"

rem Project ID GEE: atur sekali dengan  setx EE_PROJECT "project-id-anda"  lalu buka jendela baru
if "%EE_PROJECT%"=="" set /p EE_PROJECT=Masukkan Project ID Google Earth Engine:

rem Nama kecamatan boleh diberikan sebagai argumen, misalnya:  Pantau_Kubu_Raya.bat "Sungai Raya"
set "KEC=%~1"
if "%KEC%"=="" goto tanya
goto jalan

:tanya
python run_pantau.py --list
set /p KEC=Kecamatan yang dipantau (atau ketik semua):

:jalan
python run_pantau.py --project %EE_PROJECT% --kecamatan "%KEC%"
if "%~1"=="" pause
