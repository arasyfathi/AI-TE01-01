@echo off
title Multi-Agent Deforestation and Fire Monitoring System
cd /d "%~dp0Multi-Agent-System"
python -m pip install -q -r requirements.txt
python run_simulation.py --compare
pause
