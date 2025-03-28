# BSTI Toolset Installation Guide

> **Original implementation by Connor Fancy**  
> This installation guide is for the refactored version of the original BSTI toolset created by Connor Fancy.

This guide provides detailed installation instructions for the BSTI (Bulletproof SI) Toolset, a suite of utilities designed for security assessment workflows with a focus on Nessus vulnerability scanning and Plextrac reporting integration.

## Prerequisites

- Python 3.8 or higher
- Pip package manager
- Git (if cloning the repository)
- Internet connection for downloading dependencies

## Platform-Specific Requirements

### macOS

- Homebrew (recommended for installing system dependencies)
- wkhtmltopdf (required for screenshot and PDF generation)

### Linux

- Python3-venv package
- wkhtmltopdf (required for screenshot and PDF generation)

### Windows

- Microsoft Visual C++ Build Tools (for certain dependencies)
- wkhtmltopdf (required for screenshot and PDF generation)

## Installation Methods

There are several ways to install the BSTI Toolset. Choose the method that best suits your needs.

### Method 1: Using Automated Installation Scripts (Recommended)

#### Linux/macOS

1. Clone or download the BSTI Toolset repository:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Run the installation script:
   ```bash
   bash install.sh
   ```
   
3. The script will:
   - Check Python version
   - Install pip if needed
   - Create a virtual environment (recommended)
   - Install all dependencies
   - Install BSTI in development mode
   - Create convenience scripts for activation

4. If you installed in a virtual environment, activate it:
   ```bash
   source venv/bin/activate  # Linux/macOS
   ```
   
   Or use the convenience script:
   ```bash
   ./activate_bsti.sh
   ```

#### macOS Specific Setup

For macOS users, there's an additional setup script for macOS-specific dependencies:

```bash
bash macos_setup.sh
```

This script will:
- Install Homebrew (if not present)
- Install wkhtmltopdf and wkhtmltoimage
- Set up the necessary environment

#### Windows

1. Clone or download the BSTI Toolset repository:
   ```cmd
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Run the installation script:
   ```cmd
   install.bat
   ```

3. If you installed in a virtual environment, activate it:
   ```cmd
   venv\Scripts\activate.bat
   ```
   
   Or use the convenience script:
   ```cmd
   activate_bsti.bat
   ```

### Method 2: Manual Installation

If you prefer to install manually or if the automated scripts don't work for your environment:

1. Clone or download the BSTI Toolset repository:
   ```bash
   git clone <repository_url>
   cd <repository_directory>
   ```

2. Create a virtual environment (recommended):
   ```bash
   # Linux/macOS
   python3 -m venv venv
   source venv/bin/activate
   
   # Windows
   python -m venv venv
   venv\Scripts\activate
   ```

3. Upgrade pip to the latest version:
   ```bash
   pip install --upgrade pip
   ```

4. Install the package in development mode with all dependencies:
   ```bash
   pip install -e .
   ```

   Alternatively, if you just want to install dependencies without the development mode:
   ```bash
   pip install -r requirements.txt
   ```

5. For macOS users, install additional dependencies:
   ```bash
   brew install wkhtmltopdf
   ```

### Method 3: Installation for Development

If you're planning to contribute to BSTI development:

1. Follow steps 1-3 from Method 2.

2. Install with development dependencies:
   ```bash
   pip install -e ".[dev]"
   ```

3. Set up pre-commit hooks (if available):
   ```bash
   pre-commit install
   ```

## Post-Installation Setup

After installation, you'll need to configure your environment for using BSTI tools:

### Setting Up Drone Connections

1. Run the drone setup wizard:
   ```bash
   python setup_drone.py --wizard
   ```

2. Follow the prompts to enter drone name, hostname/IP, username, and password.

3. Verify your setup:
   ```bash
   python setup_drone.py --list
   ```

4. Test the connection:
   ```bash
   python nmb.py -m test-connection -d <drone_name>
   ```

### Testing the Installation

To verify that the installation was successful:

1. Use our installation verification script:
   ```bash
   python check_installation.py
   ```
   This script will check:
   - Python version
   - Virtual environment setup
   - Required dependencies
   - External tools
   - Core BSTI files
   - Drone configuration

2. Run basic tests:
   ```bash
   # Test the NMB tool
   python nmb.py --help
   
   # Test the main BSTI application
   python bsti_refactored.py --help
   
   # Test drone connection
   python nmb.py -m test-connection -d <drone_name>
   ```

## Troubleshooting

If you encounter issues during installation:

### Common Issues

1. **Python version issues**:
   - Ensure you're using Python 3.8 or higher
   - Check with `python --version` or `python3 --version`

2. **Virtual environment problems**:
   - Make sure venv is installed
   - On Ubuntu/Debian: `sudo apt-get install python3-venv`
   - On CentOS/RHEL: `sudo yum install python3-venv`

3. **Dependency conflicts**:
   - Try installing in a clean virtual environment
   - Update pip and setuptools: `pip install --upgrade pip setuptools`

4. **Import errors after installation**:
   - Check that you're in the activated virtual environment
   - Verify that all dependencies were installed correctly

5. **Permission issues**:
   - Ensure you have write permissions to the installation directory
   - Use `sudo` if installing system-wide (not recommended)

### Drone Configuration Issues

If you have problems with drone configuration:

1. Run the troubleshooting tool:
   ```bash
   python setup_drone.py --troubleshoot
   ```

2. Verify connectivity to the drone:
   ```bash
   ping <drone_hostname_or_ip>
   ```

3. Check credentials and ensure the drone configuration is correct.

## Updating BSTI

To update your BSTI installation to the latest version:

1. Pull the latest changes (if using git):
   ```bash
   git pull
   ```

2. Reinstall the package:
   ```bash
   pip install -e .
   ```

## Uninstalling

If you need to uninstall BSTI:

1. If installed in a virtual environment, simply delete the environment directory:
   ```bash
   # Deactivate first if the environment is active
   deactivate
   
   # Then remove the directory
   rm -rf venv  # Linux/macOS
   rmdir /s /q venv  # Windows
   ```

2. If installed system-wide:
   ```bash
   pip uninstall bsti-nessus
   ```

## Additional Resources

- [BSTI Documentation](https://pages.kevlar.bulletproofsi.net/iss-cs-team/delivery-toolset/BSTI/)
- [NMB README](nmb_README.md)
- [Refactored App Usage](docs/bsti_refactored_usage.md)
- [Command Reference](bsti_refactored_commands.md) 