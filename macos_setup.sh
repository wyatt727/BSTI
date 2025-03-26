#!/bin/bash

echo "===== BSTI MacOS Setup Helper ====="
echo "This script will check and install dependencies needed for BSTI on MacOS"

# Check for Homebrew
if ! command -v brew &> /dev/null; then
    echo "Homebrew not found. Installing..."
    /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    
    # Add brew to PATH
    if [[ -f ~/.zshrc ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.zshrc
        eval "$(/opt/homebrew/bin/brew shellenv)"
    elif [[ -f ~/.bash_profile ]]; then
        echo 'eval "$(/opt/homebrew/bin/brew shellenv)"' >> ~/.bash_profile
        eval "$(/opt/homebrew/bin/brew shellenv)"
    fi
    
    echo "Homebrew installed successfully."
else
    echo "✅ Homebrew is already installed."
fi

# Check for wkhtmltopdf
if ! command -v wkhtmltopdf &> /dev/null; then
    echo "wkhtmltopdf not found. Installing..."
    brew install wkhtmltopdf
    
    if [ $? -eq 0 ]; then
        echo "✅ wkhtmltopdf installed successfully."
    else
        echo "❌ Failed to install wkhtmltopdf with Homebrew."
        echo "Please download and install manually from:"
        echo "https://github.com/wkhtmltopdf/packaging/releases/download/0.12.6-2/wkhtmltox-0.12.6-2.macos-cocoa.pkg"
    fi
else
    echo "✅ wkhtmltopdf is already installed at $(which wkhtmltopdf)"
fi

# Check for wkhtmltoimage
if ! command -v wkhtmltoimage &> /dev/null; then
    echo "wkhtmltoimage not found. It should have been installed with wkhtmltopdf."
    echo "Please check your installation."
else
    echo "✅ wkhtmltoimage is already installed at $(which wkhtmltoimage)"
fi

# Check Python requirements
echo "Installing required Python packages..."
pip install -r requirements.txt

echo ""
echo "===== Setup Complete ====="
echo "If you encounter any issues with the script on MacOS:"
echo "1. Make sure wkhtmltopdf is installed correctly and accessible in your PATH"
echo "2. Try running the script with the specific path to screenshots using the -ss flag"
echo "3. Check file permissions for screenshot files"
echo ""
echo "To run the tool: python n2p_ng.py -t report -u [username] -p [password] -c [client_id] -r [report_id] -d [directory] -s [scope] -ss [screenshot_directory]"
echo ""

# Make the script executable
chmod +x macos_setup.sh 