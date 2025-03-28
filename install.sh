#!/bin/bash
# BSTI Nessus to Plextrac Converter Installation Script
# Original implementation by Connor Fancy
# This script is part of a refactored version of the original BSTI toolset
# This script installs the BSTI Nessus tool and its dependencies

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[0;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo -e "${BLUE}=== BSTI Nessus to Plextrac Converter Installation ===${NC}"
echo

# Check Python version
echo -e "${YELLOW}Checking Python version...${NC}"
if command -v python3 &>/dev/null; then
    PYTHON_CMD=python3
elif command -v python &>/dev/null; then
    # Check if python is python 3
    PYTHON_VERSION=$(python --version 2>&1)
    if [[ $PYTHON_VERSION == *"Python 3"* ]]; then
        PYTHON_CMD=python
    else
        echo -e "${RED}Error: Python 3 is required but not found.${NC}"
        echo "Please install Python 3.8 or higher and try again."
        exit 1
    fi
else
    echo -e "${RED}Error: Python 3 is required but not found.${NC}"
    echo "Please install Python 3.8 or higher and try again."
    exit 1
fi

# Check Python version is 3.8+
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | cut -d' ' -f2)
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || [ "$PYTHON_MAJOR" -eq 3 -a "$PYTHON_MINOR" -lt 8 ]; then
    echo -e "${RED}Error: Python 3.8 or higher is required.${NC}"
    echo "Current version: $PYTHON_VERSION"
    exit 1
fi

echo -e "${GREEN}Using Python $PYTHON_VERSION${NC}"

# Check if pip is installed
echo -e "${YELLOW}Checking pip installation...${NC}"
if ! $PYTHON_CMD -m pip --version &>/dev/null; then
    echo -e "${YELLOW}pip not found. Installing pip...${NC}"
    curl https://bootstrap.pypa.io/get-pip.py -o get-pip.py
    $PYTHON_CMD get-pip.py
    rm get-pip.py
fi

echo -e "${GREEN}pip is installed.${NC}"

# Create a virtual environment (optional)
echo -e "${YELLOW}Do you want to install in a virtual environment? (recommended) [Y/n]${NC}"
read -r use_venv
use_venv=${use_venv:-Y}  # Default to Yes

if [[ $use_venv =~ ^[Yy] ]]; then
    echo -e "${YELLOW}Checking venv module...${NC}"
    if ! $PYTHON_CMD -m venv --help &>/dev/null; then
        echo -e "${RED}Python venv module not found. Please install it first.${NC}"
        echo "On Ubuntu/Debian: sudo apt-get install python3-venv"
        echo "On CentOS/RHEL: sudo yum install python3-venv"
        echo "On macOS: venv should be included with Python 3"
        exit 1
    fi
    
    # Create virtual environment
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    $PYTHON_CMD -m venv venv
    
    # Activate virtual environment
    echo -e "${YELLOW}Activating virtual environment...${NC}"
    source venv/bin/activate
    
    # Update pip in the virtual environment
    echo -e "${YELLOW}Updating pip in virtual environment...${NC}"
    pip install --upgrade pip
    
    echo -e "${GREEN}Virtual environment created and activated.${NC}"
    PYTHON_CMD=python  # In the venv, we can just use 'python'
fi

# Install the package
echo -e "${YELLOW}Installing BSTI Nessus to Plextrac Converter...${NC}"
pip install -e .

# Installation complete
echo
echo -e "${GREEN}=== Installation Complete ===${NC}"
echo
echo -e "You can now run the tool using: ${BLUE}bsti-nessus${NC}"

if [[ $use_venv =~ ^[Yy] ]]; then
    echo
    echo -e "${YELLOW}Note: You need to activate the virtual environment before using the tool:${NC}"
    echo -e "  ${BLUE}source venv/bin/activate${NC}"
    
    # Create an activation script for convenience
    cat > activate_bsti.sh << EOF
#!/bin/bash
# Activate BSTI Nessus virtual environment
source "$(pwd)/venv/bin/activate"
echo "BSTI Nessus environment activated. Run 'bsti-nessus' to start."
EOF
    
    chmod +x activate_bsti.sh
    echo
    echo -e "For convenience, you can also use: ${BLUE}./activate_bsti.sh${NC}"
fi

echo
echo -e "${YELLOW}Verify your installation:${NC}"
echo -e "  ${BLUE}python check_installation.py${NC}"
echo
echo -e "${BLUE}Thank you for installing BSTI Nessus to Plextrac Converter!${NC}" 