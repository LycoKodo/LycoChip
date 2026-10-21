@echo off
rem LycoChip demo on the Windows PC: program the board, check it, draw. See projects\demo\host\demo_tui.py
py -3.12 "%~dp0projects\demo\host\demo_tui.py" %*
