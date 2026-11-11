@echo off
rem ============================================================================
rem  Genera dist\FoodSaver.exe  (ejecutar con doble clic en Windows)
rem  Requisito: Python 3.10 o superior instalado desde https://www.python.org
rem             (en el instalador deja marcado "tcl/tk and IDLE" y "Add to PATH").
rem ============================================================================
setlocal
cd /d "%~dp0"

set "PY=python"
where py >nul 2>nul && set "PY=py -3"

echo [1/3] Instalando PyInstaller...
%PY% -m pip install --quiet -r requirements-dev.txt
if errorlevel 1 goto :error

echo [2/3] Ejecutando pruebas...
%PY% -m unittest discover -s tests
if errorlevel 1 goto :error

echo [3/3] Creando el .exe (puede tardar un minuto)...
%PY% -m PyInstaller --noconfirm --clean --onefile --windowed --icon assets\icono.ico --name FoodSaver main.py
if errorlevel 1 goto :error

echo.
echo Listo: dist\FoodSaver.exe
pause
exit /b 0

:error
echo.
echo Algo fallo. Revisa el mensaje de arriba.
pause
exit /b 1
