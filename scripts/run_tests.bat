@echo off
REM Quick test runner script for jsweb (Windows)

setlocal enabledelayedexpansion

echo.
echo ================================================
echo JsWeb Test Suite
echo ================================================
echo.

REM Check if virtual environment exists
if not exist "venv\" (
    if not exist ".venv\" (
        echo Creating virtual environment...
        python -m venv venv
        call venv\Scripts\activate.bat
        python -m pip install --upgrade pip
    ) else (
        call .venv\Scripts\activate.bat
    )
) else (
    call venv\Scripts\activate.bat
)

REM Install dependencies
echo Installing dependencies...
pip install -e ".[dev]"

REM Run tests
echo.
echo Running tests...
echo.
pytest 

REM Check exit code
if %ERRORLEVEL% EQU 0 (
    echo.
    echo Tests passed!
    echo Coverage report generated in htmlcov\index.html
) else (
    echo.
    echo Tests failed!
    exit /b 1
)

echo.
echo ================================================
echo.

pause
