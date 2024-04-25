@echo off

echo Starting UI...
start "UI Application" cmd /c python -m ui.app

echo Starting Data Acquisition...
start "Data Acquisition" cmd /c python -m tec_interface

echo All systems running. Stop the applications by closing their respective terminal.
pause
