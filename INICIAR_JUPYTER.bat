@echo off
cd /d "%~dp0"
echo Iniciando proyecto Memoria Chilena desde: %CD%
python -m pip install -r requirements.txt
if errorlevel 1 (
  echo Error instalando dependencias. Verifica que Python este instalado.
  pause
  exit /b 1
)
python -m jupyter lab
if errorlevel 1 (
  echo No se pudo iniciar JupyterLab. Comprueba Python y Jupyter.
  pause
  exit /b 1
)
