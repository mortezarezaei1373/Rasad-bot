@echo off
cd /d C:\Users\Administrator\Desktop\Rasadbot
:loop
venv\Scripts\python.exe bot.py
timeout /t 10
goto loop