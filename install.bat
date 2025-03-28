@echo off
REM BSTI Nessus to Plextrac Converter Installation Script for Windows
REM This script installs the BSTI Nessus tool and its dependencies

echo ==== BSTI Nessus to Plextrac Converter Installation ====
echo.

REM Check Python version
echo Checking Python version...
where python >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo Error: Python is not found in your PATH.
    echo Please install Python 3.8 or higher and try again.
    pause
    exit /b 1
)

REM Check Python version is 3.8+
for /f "tokens=2" %%I in ('python --version 2^>^&1') do set PYTHON_VERSION=%%I
for /f "tokens=1,2 delims=." %%a in ("%PYTHON_VERSION%") do (
    set PYTHON_MAJOR=%%a
    set PYTHON_MINOR=%%b
)

if %PYTHON_MAJOR% LSS 3 (
    echo Error: Python 3.8 or higher is required.
    echo Current version: %PYTHON_VERSION%
    pause
    exit /b 1
) else (
    if %PYTHON_MAJOR% EQU 3 (
        if %PYTHON_MINOR% LSS 8 (
            echo Error: Python 3.8 or higher is required.
            echo Current version: %PYTHON_VERSION%
            pause
            exit /b 1
        )
    )
)

echo Using Python %PYTHON_VERSION%

REM Check if pip is installed
echo Checking pip installation...
python -m pip --version >nul 2>&1
if %ERRORLEVEL% neq 0 (
    echo pip not found. Installing pip...
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    python get-pip.py
    del get-pip.py
)

echo pip is installed.

REM Create a virtual environment (optional)
set /p use_venv=Do you want to install in a virtual environment? (recommended) [Y/n]: 
if not defined use_venv set use_venv=Y

if /i "%use_venv%"=="Y" (
    echo Checking venv module...
    python -m venv --help >nul 2>&1
    if %ERRORLEVEL% neq 0 (
        echo Error: Python venv module not found. 
        echo This should be included with Python 3 installation.
        pause
        exit /b 1
    )
    
    REM Create virtual environment
    echo Creating virtual environment...
    python -m venv venv
    
    REM Activate virtual environment
    echo Activating virtual environment...
    call venv\Scripts\activate.bat
    
    REM Update pip in the virtual environment
    echo Updating pip in virtual environment...
    pip install --upgrade pip
    
    echo Virtual environment created and activated.
)

REM Install the package
echo Installing BSTI Nessus to Plextrac Converter...
pip install -e .

REM Installation complete
echo.
echo ==== Installation Complete ====
echo.
echo You can now run the tool using: bsti-nessus

if /i "%use_venv%"=="Y" (
    echo.
    echo Note: You need to activate the virtual environment before using the tool:
    echo   venv\Scripts\activate.bat
    
    REM Create an activation script for convenience
    (
        echo @echo off
        echo REM Activate BSTI Nessus virtual environment
        echo call "%CD%\venv\Scripts\activate.bat"
        echo echo BSTI Nessus environment activated. Run 'bsti-nessus' to start.
    ) > activate_bsti.bat
    
    echo.
    echo For convenience, you can also use: activate_bsti.bat
)

echo.
echo Note: You can verify your installation by running:
echo   python check_installation.py
echo.
echo Thank you for installing BSTI Nessus to Plextrac Converter!
pause 