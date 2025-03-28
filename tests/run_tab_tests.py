#!/usr/bin/env python3
# Test runner script for BSTI Tab Components
# This script runs all tests for the newly implemented tab components

import os
import sys
import subprocess
import argparse
from datetime import datetime

# Try to import testing modules, but provide fallbacks
try:
    import pytest
    PYTEST_AVAILABLE = True
except ImportError:
    PYTEST_AVAILABLE = False
    print("Warning: pytest not available. Falling back to unittest.")

try:
    import coverage
    COVERAGE_AVAILABLE = True
except ImportError:
    COVERAGE_AVAILABLE = False
    print("Warning: coverage not available. Test coverage reporting disabled.")

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Run tab component tests with coverage reporting')
    parser.add_argument('--html', action='store_true', help='Generate HTML coverage report')
    parser.add_argument('--xml', action='store_true', help='Generate XML coverage report')
    parser.add_argument('--verbose', '-v', action='store_true', help='Run tests in verbose mode')
    parser.add_argument('--test-file', '-t', help='Run tests only for a specific file')
    parser.add_argument('--component', '-c', choices=['home', 'module', 'logs', 'all'], default='all',
                        help='Specify which component to test')
    return parser.parse_args()

def setup_coverage():
    """Set up coverage measurement."""
    if COVERAGE_AVAILABLE:
        cov = coverage.Coverage(
            source=['src/components/home_tab.py', 
                   'src/components/module_editor_tab.py', 
                   'src/components/view_logs_tab.py'],
            omit=['*/tests/*', '*/venv/*', '*/site-packages/*'],
            config_file='.coveragerc' if os.path.exists('.coveragerc') else None
        )
        cov.start()
        return cov
    return None

def run_tests_with_pytest(verbose=False, test_file=None, component='all'):
    """Run pytest with specified options."""
    args = ['-xvs'] if verbose else ['-x']
    
    if test_file:
        args.append(test_file)
    else:
        if component == 'home':
            args.append('tests/test_home_tab.py')
        elif component == 'module':
            args.append('tests/test_module_editor_tab.py')
        elif component == 'logs':
            args.append('tests/test_view_logs_tab.py')
        else:  # 'all'
            args.extend(['tests/test_home_tab.py', 'tests/test_module_editor_tab.py', 'tests/test_view_logs_tab.py'])
    
    try:
        result = pytest.main(args)
        return result == 0
    except Exception as e:
        print(f"Error running tests with pytest: {e}")
        return False

def run_tests_with_unittest(verbose=False, test_file=None, component='all'):
    """Run tests using unittest module."""
    import unittest
    
    if test_file:
        test_suite = unittest.defaultTestLoader.discover(os.path.dirname(test_file), 
                                                       pattern=os.path.basename(test_file))
    else:
        if component == 'home':
            test_suite = unittest.defaultTestLoader.loadTestsFromName('test_home_tab')
        elif component == 'module':
            test_suite = unittest.defaultTestLoader.loadTestsFromName('test_module_editor_tab')
        elif component == 'logs':
            test_suite = unittest.defaultTestLoader.loadTestsFromName('test_view_logs_tab')
        else:  # 'all'
            test_suite = unittest.defaultTestLoader.discover('.', pattern='test_*_tab.py')
    
    verbosity = 2 if verbose else 1
    runner = unittest.TextTestRunner(verbosity=verbosity)
    result = runner.run(test_suite)
    return result.wasSuccessful()

def run_tests(verbose=False, test_file=None, component='all'):
    """Run tests with the appropriate test runner."""
    if PYTEST_AVAILABLE:
        return run_tests_with_pytest(verbose=verbose, test_file=test_file, component=component)
    else:
        return run_tests_with_unittest(verbose=verbose, test_file=test_file, component=component)

def generate_reports(cov, html=False, xml=False):
    """Generate coverage reports."""
    if not cov:
        print("No coverage data available.")
        return
    
    cov.stop()
    cov.save()
    
    print("\nCoverage Summary:")
    cov.report()
    
    if html:
        html_dir = os.path.join(os.getcwd(), 'coverage_html_report')
        cov.html_report(directory=html_dir)
        print(f"\nHTML report generated at {html_dir}")
    
    if xml:
        xml_file = os.path.join(os.getcwd(), 'coverage.xml')
        cov.xml_report(outfile=xml_file)
        print(f"\nXML report generated at {xml_file}")

def run_manual_tests():
    """Run basic manual tests on the tab components."""
    print("\nRunning basic manual tests on tab components:")
    
    tests = [
        ("Testing Home Tab existence", ["python", "-c", "from src.components.home_tab import HomeTab; print('Home Tab exists!')"], True),
        ("Testing Module Editor Tab existence", ["python", "-c", "from src.components.module_editor_tab import ModuleEditorTab; print('Module Editor Tab exists!')"], True),
        ("Testing View Logs Tab existence", ["python", "-c", "from src.components.view_logs_tab import ViewLogsTab; print('View Logs Tab exists!')"], True),
        ("Verifying PyQt5 installation", ["python", "-c", "from PyQt5.QtWidgets import QApplication; print('PyQt5 is installed!')"], True)
    ]
    
    all_passed = True
    for test_name, command, required in tests:
        print(f"\n{test_name}:")
        try:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode == 0:
                print(f"✅ Success! ({result.returncode})")
                # Print a snippet of the output
                output_preview = result.stdout.strip().split('\n')[:3]
                print("\n".join(output_preview))
                if len(result.stdout.strip().split('\n')) > 3:
                    print("...")
            else:
                print(f"❌ Failed with code {result.returncode}")
                print(result.stderr)
                if required:
                    all_passed = False
        except Exception as e:
            print(f"❌ Error: {e}")
            if required:
                all_passed = False
    
    return all_passed

def main():
    """Main function to run tests with coverage."""
    args = parse_args()
    
    # Print header
    print("=" * 80)
    print(f"Running BSTI Tab Component tests - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"Testing {'all components' if args.component == 'all' else args.component + ' component'}")
    print("=" * 80)
    
    # Setup coverage if available
    cov = setup_coverage() if args.html or args.xml else None
    
    # Run automated tests
    print("\nRunning automated tests:")
    auto_success = run_tests(verbose=args.verbose, test_file=args.test_file, component=args.component)
    
    # Generate coverage reports if available
    if cov:
        generate_reports(cov, html=args.html, xml=args.xml)
    
    # Run manual tests
    manual_success = run_manual_tests()
    
    # Print summary
    print("\n" + "=" * 80)
    if auto_success and manual_success:
        print("✅ All tests passed successfully!")
    else:
        print("❌ Some tests failed!")
    print("=" * 80)
    
    return 0 if auto_success and manual_success else 1

if __name__ == '__main__':
    sys.exit(main()) 