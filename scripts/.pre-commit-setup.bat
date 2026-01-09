@echo off
REM Pre-commit hooks setup script for jsweb (Windows)
REM This script sets up pre-commit hooks to automatically run code quality checks

setlocal enabledelayedexpansion

echo 🔧 Setting up pre-commit hooks for jsweb...

REM Check if pre-commit is installed
where pre-commit >nul 2>nul
if errorlevel 1 (
    echo 📦 Installing pre-commit...
    pip install pre-commit
)

REM Install the git hooks
echo 📝 Installing git pre-commit hooks...
pre-commit install
pre-commit install --hook-type pre-push

REM Optional: Run all hooks on all files to check current state
echo 🔍 Running hooks on all files (this may take a moment)...
pre-commit run --all-files || exit /b 0

echo ✅ Pre-commit hooks setup complete!
echo.
echo 📚 Usage:
echo   - Hooks will run automatically before each commit
echo   - Run manually: pre-commit run --all-files
echo   - Skip hooks: git commit --no-verify
echo   - Update hooks: pre-commit autoupdate
echo.

pause
