@echo off
setlocal

rem Проверяем наличие Python в виртуальном окружении проекта
if exist ".venv\Scripts\python.exe" (
    set "PY_EXE=.venv\Scripts\python.exe"
) else if exist "venv\Scripts\python.exe" (
    set "PY_EXE=venv\Scripts\python.exe"
) else (
    set "PY_EXE=python"
)

rem Запуск эмулятора с передачей всех аргументов
"%PY_EXE%" -m src.main %*
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Script finished with error code %ERRORLEVEL%.
    pause
)

endlocal