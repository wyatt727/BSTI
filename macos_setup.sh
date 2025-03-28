#!/bin/bash
# BSTI MacOS Setup Helper
# Original BSTI implementation by Connor Fancy
# This script is part of a refactored version of the original BSTI toolset

echo "===== BSTI MacOS Setup Helper ====="
echo "This script will check and install dependencies needed for BSTI on MacOS"
echo "Original BSTI implementation by Connor Fancy"

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

# Ask if the user wants to install in a virtual environment
echo ""
echo "Would you like to install BSTI in a virtual environment? (recommended) [Y/n]"
read -r use_venv
use_venv=${use_venv:-Y}  # Default to Yes

if [[ $use_venv =~ ^[Yy] ]]; then
    echo "Creating and activating virtual environment..."
    python3 -m venv venv
    source venv/bin/activate
    
    # Upgrade pip
    echo "Upgrading pip..."
    pip install --upgrade pip
    
    echo "✅ Virtual environment created and activated."
else
    echo "Proceeding with system-wide installation."
fi

# Ask if the user wants to install in development mode
echo ""
echo "Would you like to install BSTI in development mode? (editable installation) [Y/n]"
read -r dev_mode
dev_mode=${dev_mode:-Y}  # Default to Yes

if [[ $dev_mode =~ ^[Yy] ]]; then
    echo "Installing BSTI in development mode..."
    pip install -e .
    echo "✅ BSTI installed in development mode."
else
    echo "Installing BSTI dependencies only..."
    pip install -r requirements.txt
    echo "✅ BSTI dependencies installed."
fi

echo ""
echo "===== Setup Complete ====="
echo "If you encounter any issues with the script on MacOS:"
echo "1. Make sure wkhtmltopdf is installed correctly and accessible in your PATH"
echo "2. Try running the script with the specific path to screenshots using the -ss flag"
echo "3. Check file permissions for screenshot files"
echo ""
echo "To run the main BSTI application:"
echo "python bsti_refactored.py"
echo ""
echo "To run the NMB tool:"
echo "python nmb.py --help"
echo ""
echo "To set up drone connections:"
echo "python setup_drone.py --wizard"
echo ""

# Create an activation script for convenience if using venv
if [[ $use_venv =~ ^[Yy] ]]; then
    cat > activate_bsti.sh << EOF
#!/bin/bash
# Activate BSTI virtual environment
source "$(pwd)/venv/bin/activate"
echo "BSTI environment activated. Run 'python bsti_refactored.py' to start the main application."
EOF
    
    chmod +x activate_bsti.sh
    echo "For convenience, you can use './activate_bsti.sh' to activate the virtual environment in the future."
fi

# Make the script executable
chmod +x macos_setup.sh 