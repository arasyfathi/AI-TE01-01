@echo off
title CardioExpert CDSS — Web Application Launcher
color 0B
cls
echo.
echo  ================================================================
echo    CardioExpert CDSS — Clinical Decision Support System
echo    Sistem Pakar Diagnosis ^& Rekomendasi Pengobatan Jantung
echo  ================================================================
echo.
echo  [*] Membuka aplikasi web di browser default...
echo.

REM Buka index.html langsung di browser (tanpa server)
set "WEBDIR=%~dp0Expert-System-Implementation-main\web-ui"
set "HTMLFILE=%WEBDIR%\index.html"

if exist "%HTMLFILE%" (
    start "" "%HTMLFILE%"
    echo  [OK] Aplikasi berhasil dibuka: %HTMLFILE%
    echo.
    echo  Jika tidak otomatis terbuka, buka file berikut secara manual:
    echo  %HTMLFILE%
) else (
    echo  [ERROR] File tidak ditemukan: %HTMLFILE%
    echo  Pastikan folder web-ui ada di direktori Expert-System-Implementation-main
)

echo.
echo  ================================================================
echo    Informasi Tambahan:
echo    - File: Expert-System-Implementation-main\web-ui\index.html
echo    - C++ EXE: Expert-System-Implementation-main\Project1-SubmittedFiles\expert_system.exe
echo  ================================================================
echo.
pause
