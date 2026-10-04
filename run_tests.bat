@echo off
setlocal EnableExtensions DisableDelayedExpansion
pushd "%~dp0"
if errorlevel 1 exit /b 2

rem Optional override: set TEST_PYTHON=C:\path\to\python.exe
if defined TEST_PYTHON (
    set "TEST_INTERPRETER=%TEST_PYTHON%"
    goto interpreter_selected
)
if defined VIRTUAL_ENV if exist "%VIRTUAL_ENV%\Scripts\python.exe" (
    set "TEST_INTERPRETER=%VIRTUAL_ENV%\Scripts\python.exe"
    goto interpreter_selected
)
if exist ".venv\Scripts\python.exe" (
    set "TEST_INTERPRETER=%CD%\.venv\Scripts\python.exe"
    goto interpreter_selected
)
if exist "venv\Scripts\python.exe" (
    set "TEST_INTERPRETER=%CD%\venv\Scripts\python.exe"
    goto interpreter_selected
)
set "TEST_INTERPRETER=python"

:interpreter_selected
echo Python: "%TEST_INTERPRETER%"
"%TEST_INTERPRETER%" -c "import pytest, pytestqt, pytest_cov, regex; from PyQt6 import QtCore; assert QtCore.QT_VERSION >= 0x060900, 'Qt 6.9+ required'"
if errorlevel 1 goto missing_dependencies

rem Keep pytest temporary files inside this project.
if not exist ".pytest_tmp" mkdir ".pytest_tmp"
if not exist ".pytest_tmp\" goto temp_directory_error

:select_test_temp
set "TEST_TEMP_DIR=%CD%\.pytest_tmp\run_%RANDOM%_%RANDOM%"
if exist "%TEST_TEMP_DIR%" goto select_test_temp

set "PYTEST_QT_API=pyqt6"
if not defined QT_QPA_PLATFORM set "QT_QPA_PLATFORM=offscreen"
"%TEST_INTERPRETER%" -m pytest tests --basetemp="%TEST_TEMP_DIR%" -p no:cacheprovider --cov=src --cov-branch --cov-report=term-missing --cov-report=html:reports/htmlcov --junitxml=reports/junit.xml %*
set "TEST_EXIT_CODE=%ERRORLEVEL%"
echo.
echo Test exit code: %TEST_EXIT_CODE%
echo HTML coverage: reports\htmlcov\index.html
goto finish

:temp_directory_error
echo.
echo Cannot create temporary directory: "%CD%\.pytest_tmp"
set "TEST_EXIT_CODE=2"
goto finish

:missing_dependencies
echo.
echo Python or test dependencies are unavailable.
echo Install dependencies with the SAME interpreter:
echo "%TEST_INTERPRETER%" -m pip install -r requirements-test.txt
set "TEST_EXIT_CODE=2"

:finish
popd
if not "%TEST_NO_PAUSE%"=="1" pause
exit /b %TEST_EXIT_CODE%
