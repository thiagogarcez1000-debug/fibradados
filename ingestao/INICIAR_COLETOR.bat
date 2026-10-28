@echo off
REM FibraDados - inicia o coletor de varreduras (card C04). Deixe esta janela aberta.
cd /d "%~dp0\.."
python ingestao\coletor.py --intervalo 300
pause
