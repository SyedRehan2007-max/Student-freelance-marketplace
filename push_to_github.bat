@echo off
title Push Project to GitHub
echo ===================================================
echo Pushing Student Freelance Marketplace to GitHub...
echo Repository: https://github.com/SyedRehan2007-max/Student-freelance-marketplace.git
echo ===================================================
echo.
cd /d "%~dp0"
echo Running: git push origin main
echo.
git push origin main
echo.
if %ERRORLEVEL% equ 0 (
    echo ===================================================
    echo SUCCESS: Project successfully pushed to GitHub!
    echo ===================================================
) else (
    echo ===================================================
    echo Push incomplete or requires GitHub login.
    echo Please make sure you are signed into GitHub.
    echo ===================================================
)
echo.
pause
