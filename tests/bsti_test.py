#!/usr/bin/env python3
"""
BSTI Testing Script

This script is designed to diagnose the segmentation fault occurring in the BSTI application.
It performs step-by-step tests to isolate the component causing the crash.
"""

import os
import sys
import logging
import platform
import subprocess
import traceback
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('bsti_test_results.log')
    ]
)
logger = logging.getLogger("bsti_test")

def print_separator():
    """Print a separator line for better readability."""
    logger.info("=" * 70)

def print_system_info():
    """Print relevant system information."""
    logger.info("System Information:")
    logger.info(f"OS: {platform.system()} {platform.release()} ({platform.version()})")
    logger.info(f"Python: {platform.python_version()}")
    logger.info(f"Platform: {platform.platform()}")
    logger.info(f"Machine: {platform.machine()}")
    logger.info(f"Processor: {platform.processor()}")
    
    # Check for Qt version
    try:
        import PyQt5.QtCore
        logger.info(f"PyQt5 version: {PyQt5.QtCore.PYQT_VERSION_STR}")
        logger.info(f"Qt version: {PyQt5.QtCore.QT_VERSION_STR}")
    except ImportError:
        logger.error("PyQt5 is not installed")
    
    print_separator()

def check_dependencies():
    """Check if all required dependencies are installed."""
    logger.info("Checking dependencies...")
    
    try:
        import pkg_resources
        required_packages = []
        
        # Read requirements from requirements.txt
        try:
            with open('requirements.txt', 'r') as f:
                required_packages = [line.strip() for line in f if line.strip() and not line.startswith('#')]
        except (IOError, FileNotFoundError):
            logger.error("Could not read requirements.txt")
        
        # Check each package
        missing_packages = []
        for package in required_packages:
            package_name = package.split('==')[0]
            try:
                pkg_resources.get_distribution(package_name)
                logger.info(f"✓ {package}")
            except pkg_resources.DistributionNotFound:
                logger.error(f"✗ {package} is missing")
                missing_packages.append(package)
        
        if missing_packages:
            logger.warning(f"Missing packages: {', '.join(missing_packages)}")
            logger.info("Installing missing packages...")
            subprocess.run([sys.executable, '-m', 'pip', 'install'] + missing_packages)
            logger.info("Packages installed. Please run this script again.")
            return False
        else:
            logger.info("All required packages are installed.")
            return True
    
    except Exception as e:
        logger.error(f"Error checking dependencies: {str(e)}")
        return False
    
    print_separator()

def check_fonts():
    """Check available fonts and identify if Segoe UI is present."""
    logger.info("Checking available fonts...")
    
    try:
        from PyQt5.QtGui import QFontDatabase
        from PyQt5.QtWidgets import QApplication
        
        # Create a minimal Qt application
        app = QApplication([])
        
        # Get all available font families
        font_db = QFontDatabase()
        available_fonts = font_db.families()
        
        logger.info(f"Total fonts available: {len(available_fonts)}")
        
        # Check if Segoe UI is present
        if "Segoe UI" in available_fonts:
            logger.info("✓ 'Segoe UI' font is available")
        else:
            logger.warning("✗ 'Segoe UI' font is NOT available")
            segoe_alternatives = [font for font in available_fonts if 'segoe' in font.lower()]
            if segoe_alternatives:
                logger.info(f"Similar fonts: {', '.join(segoe_alternatives)}")
            
            # Log some common system fonts that could be used as fallbacks
            common_fonts = ['Arial', 'Helvetica', 'Tahoma', 'Verdana', 'San Francisco', '.SF NS Text', 'Lucida Grande']
            available_common = [font for font in common_fonts if font in available_fonts]
            logger.info(f"Available common fonts that could be used as alternatives: {', '.join(available_common)}")
            
            # Suggest a fix
            logger.info("Suggested fix: Modify src/config/config.py to use available fonts")
    
    except Exception as e:
        logger.error(f"Error checking fonts: {str(e)}")
    
    print_separator()

def test_stylesheet_loading():
    """Test loading the stylesheet without starting the full application."""
    logger.info("Testing stylesheet loading...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        from PyQt5.QtCore import QFile, QTextStream
        
        # Create a minimal Qt application
        app = QApplication([])
        
        # Try to load the stylesheet
        stylesheet_path = os.path.join('src', 'config', 'styles.qss')
        
        if os.path.exists(stylesheet_path):
            logger.info(f"Stylesheet found at {stylesheet_path}")
            
            file = QFile(stylesheet_path)
            if file.open(QFile.ReadOnly | QFile.Text):
                stream = QTextStream(file)
                stylesheet = stream.readAll()
                file.close()
                
                logger.info(f"Stylesheet loaded successfully ({len(stylesheet)} characters)")
                
                # Try applying the stylesheet
                try:
                    app.setStyleSheet(stylesheet)
                    logger.info("Stylesheet applied successfully")
                except Exception as e:
                    logger.error(f"Error applying stylesheet: {str(e)}")
            else:
                logger.error("Could not open stylesheet file")
        else:
            logger.error(f"Stylesheet not found at {stylesheet_path}")
    
    except Exception as e:
        logger.error(f"Error testing stylesheet: {str(e)}")
    
    print_separator()

def test_minimal_application():
    """Test creating a minimal Qt application with custom font."""
    logger.info("Testing minimal Qt application with custom font...")
    
    try:
        from PyQt5.QtWidgets import QApplication, QMainWindow, QLabel
        from PyQt5.QtGui import QFont
        import signal
        
        # Set up signal handler to catch segmentation faults
        def handle_segfault(signum, frame):
            logger.error("Segmentation fault caught during minimal application test")
            print_backtrace()
            sys.exit(1)
        
        signal.signal(signal.SIGSEGV, handle_segfault)
        
        # Create a minimal Qt application with a main window and label
        app = QApplication([])
        
        # Test without custom font first
        try:
            logger.info("Testing without custom font...")
            window = QMainWindow()
            window.setWindowTitle("Test Window")
            label = QLabel("Hello World")
            window.setCentralWidget(label)
            window.resize(300, 200)
            logger.info("Basic QMainWindow created successfully")
        except Exception as e:
            logger.error(f"Error creating basic window: {str(e)}")
        
        # Now test with a custom font
        try:
            logger.info("Testing with custom font...")
            font_family = "Arial, Helvetica, sans-serif"  # Safe fallback fonts
            font = QFont(font_family.split(",")[0].strip())
            font.setPointSize(13)
            app.setFont(font)
            logger.info("Custom font applied successfully")
        except Exception as e:
            logger.error(f"Error applying custom font: {str(e)}")
        
        logger.info("Minimal Qt application test completed successfully")
    
    except Exception as e:
        logger.error(f"Error in minimal application test: {str(e)}")
    
    print_separator()

def test_component_by_component():
    """Test each major component of the application to isolate the issue."""
    logger.info("Testing components one by one...")
    
    try:
        from PyQt5.QtWidgets import QApplication
        app = QApplication([])
        
        # Test 1: MainWindow creation (without loading all tabs)
        try:
            logger.info("Test 1: Creating partial MainWindow...")
            
            # Create a simplified main window without tabs
            code = """
import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout
from PyQt5.QtCore import QFile, QTextStream
from PyQt5.QtGui import QFont

# Add current directory to path
sys.path.insert(0, os.getcwd())

# Create a simplified main window
class TestMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("BSTI Test")
        self.setGeometry(100, 100, 800, 600)
        
        # Create central widget
        self.central_widget = QWidget()
        self.layout = QVBoxLayout(self.central_widget)
        self.setCentralWidget(self.central_widget)

# Run the test
app = QApplication(sys.argv)
window = TestMainWindow()
# Just create the window but don't show it
"""
            # Execute the test code
            exec(code)
            logger.info("✓ MainWindow creation successful")
            
            # Test 2: Try to load and apply the stylesheet
            logger.info("Test 2: Loading and applying stylesheet...")
            
            code = """
import os
import sys
from PyQt5.QtWidgets import QApplication, QMainWindow
from PyQt5.QtCore import QFile, QTextStream

# Create a minimal application
app = QApplication(sys.argv)

# Load the stylesheet
stylesheet_path = os.path.join('src', 'config', 'styles.qss')
if os.path.exists(stylesheet_path):
    file = QFile(stylesheet_path)
    if file.open(QFile.ReadOnly | QFile.Text):
        stream = QTextStream(file)
        stylesheet = stream.readAll()
        file.close()
        
        # Apply the stylesheet
        app.setStyleSheet(stylesheet)
"""
            # Execute the test code
            exec(code)
            logger.info("✓ Stylesheet loading and application successful")
            
            # Test 3: Font loading
            logger.info("Test 3: Testing font loading...")
            
            code = """
import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont, QFontDatabase

# Create a minimal application
app = QApplication(sys.argv)

# Load font configuration
try:
    # Import the config module for font settings
    from src.config import config
    
    # Get the font family and size
    font_family = config.FONT_FAMILY
    font_size = config.FONT_SIZE
    
    # Create font object
    default_font = QFont(font_family.split(",")[0].strip())
    default_font.setPointSize(font_size)
    
    # Apply font to application
    app.setFont(default_font)
except ImportError:
    # Fall back to hardcoded values from config.py
    font_family = "Segoe UI, Arial, sans-serif"
    font_size = 13
    
    # Create font object
    default_font = QFont(font_family.split(",")[0].strip())
    default_font.setPointSize(font_size)
    
    # Apply font to application
    app.setFont(default_font)
"""
            # Execute the test code
            try:
                exec(code)
                logger.info("✓ Font loading successful")
            except Exception as e:
                logger.error(f"✗ Font loading failed: {str(e)}")
                logger.info("This is likely the cause of the segmentation fault")
                
                # Test with a modified font setting
                logger.info("Test 3b: Testing with alternative font...")
                code = """
import os
import sys
from PyQt5.QtWidgets import QApplication
from PyQt5.QtGui import QFont

# Create a minimal application
app = QApplication(sys.argv)

# Use a safe alternative
font_family = "Arial, Helvetica, sans-serif"
font_size = 13

# Create font object
default_font = QFont(font_family.split(",")[0].strip())
default_font.setPointSize(font_size)

# Apply font to application
app.setFont(default_font)
"""
                try:
                    exec(code)
                    logger.info("✓ Alternative font loading successful")
                except Exception as e:
                    logger.error(f"✗ Alternative font loading failed: {str(e)}")
            
        except Exception as e:
            logger.error(f"Component testing failed: {str(e)}")
    
    except Exception as e:
        logger.error(f"Error in component testing: {str(e)}")
    
    print_separator()

def generate_modified_config():
    """Generate a modified config.py with font fixes."""
    logger.info("Generating modified config.py with font fixes...")
    
    from PyQt5.QtGui import QFontDatabase
    from PyQt5.QtWidgets import QApplication
    
    # Create a minimal Qt application
    app = QApplication([])
    
    # Get all available font families
    font_db = QFontDatabase()
    available_fonts = font_db.families()
    
    # Choose a good fallback font
    system_font = None
    for font in ['Arial', 'Helvetica', 'Tahoma', 'Verdana', 'San Francisco', '.SF NS Text', 'Lucida Grande']:
        if font in available_fonts:
            system_font = font
            break
    
    if not system_font:
        system_font = available_fonts[0] if available_fonts else "Arial"
    
    logger.info(f"Selected system font: {system_font}")
    
    # Read the original config.py
    try:
        with open(os.path.join('src', 'config', 'config.py'), 'r') as f:
            config_content = f.read()
        
        # Replace the font family line
        old_font_line = 'FONT_FAMILY = "Segoe UI, Arial, sans-serif"'
        new_font_line = f'FONT_FAMILY = "{system_font}, Arial, sans-serif"'
        modified_content = config_content.replace(old_font_line, new_font_line)
        
        # Write the modified config to a new file
        with open('config_fixed.py', 'w') as f:
            f.write(modified_content)
        
        logger.info("Modified config saved to config_fixed.py")
        logger.info(f"Original font setting: {old_font_line}")
        logger.info(f"Modified font setting: {new_font_line}")
        
        # Provide instructions
        logger.info("\nTo fix the font issue, run these commands:")
        logger.info("cp config_fixed.py src/config/config.py")
        
    except Exception as e:
        logger.error(f"Error generating modified config: {str(e)}")
    
    print_separator()

def run_final_test():
    """Run a final test with the fixed configuration if available."""
    if os.path.exists('config_fixed.py'):
        logger.info("Running final test with fixed configuration...")
        
        try:
            import shutil
            
            # Backup original config
            if not os.path.exists('src/config/config.py.bak'):
                shutil.copy('src/config/config.py', 'src/config/config.py.bak')
                logger.info("Original config backed up to src/config/config.py.bak")
            
            # Copy the fixed config
            shutil.copy('config_fixed.py', 'src/config/config.py')
            logger.info("Fixed config applied")
            
            # Try to run the application with a timeout
            logger.info("Attempting to start BSTI with fixed config...")
            try:
                result = subprocess.run(
                    [sys.executable, '-m', 'src'],
                    timeout=5,
                    stderr=subprocess.PIPE,
                    stdout=subprocess.PIPE
                )
                logger.info(f"Return code: {result.returncode}")
                if result.stdout:
                    logger.info(f"Output: {result.stdout.decode('utf-8')}")
                if result.stderr:
                    logger.info(f"Error: {result.stderr.decode('utf-8')}")
            except subprocess.TimeoutExpired:
                logger.info("Application started and ran for 5 seconds without crashing!")
            except Exception as e:
                logger.error(f"Error running application: {str(e)}")
            
            # Restore original config
            shutil.copy('src/config/config.py.bak', 'src/config/config.py')
            logger.info("Original config restored")
            
        except Exception as e:
            logger.error(f"Error in final test: {str(e)}")
        
        print_separator()

def print_backtrace():
    """Print the current backtrace."""
    logger.error("Backtrace:")
    traceback.print_stack()

def run_all_tests():
    """Run all diagnostic tests."""
    logger.info("Starting BSTI diagnostic tests")
    print_separator()
    
    # Run all tests
    print_system_info()
    if check_dependencies():
        check_fonts()
        test_stylesheet_loading()
        test_minimal_application()
        test_component_by_component()
        generate_modified_config()
        run_final_test()
    
    logger.info("BSTI diagnostic tests completed")
    logger.info("Check bsti_test_results.log for detailed results")

if __name__ == "__main__":
    run_all_tests() 