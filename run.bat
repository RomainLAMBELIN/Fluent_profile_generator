@echo off
REM Lancement du generateur de profils Fluent sous Windows.
REM Aucune installation n'est necessaire : ce script appelle launch.py,
REM qui rend lui-meme le projet importable.

setlocal
cd /d "%~dp0"

echo Demarrage du generateur de profils Fluent...
echo.

set "PYEXE="
where python >nul 2>&1 && set "PYEXE=python"
if defined PYEXE goto :found

py -3 --version >nul 2>&1 && set "PYEXE=py -3"
if defined PYEXE goto :found

goto :nopython

:found
%PYEXE% launch.py %*
if errorlevel 1 goto :failed
goto :done

:nopython
echo ERREUR : aucun interpreteur Python n'a ete trouve dans le PATH.
echo.
echo Si vous utilisez Anaconda, ouvrez "Anaconda Prompt" puis tapez :
echo     cd /d "%~dp0"
echo     python launch.py
echo.
pause
exit /b 1

:failed
echo.
echo L'application s'est terminee avec une erreur.
echo Pour un diagnostic complet, lancez :
echo     %PYEXE% launch.py --check
echo.
pause
exit /b 1

:done
endlocal
