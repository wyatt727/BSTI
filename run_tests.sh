#!/bin/bash
# Simple script to run tests for BSTI
# This script helps to run tests from the root directory

set -e

# Parse command line arguments
SKIP_NMB=false
SKIP_UI=false
SKIP_MODULE=false
VERBOSE=false
HTML_REPORT=false
XML_REPORT=false
TEST_FILE=""

print_usage() {
    echo "Usage: $0 [options]"
    echo "Options:"
    echo "  -h, --help                 Show this help message"
    echo "  -v, --verbose              Run tests in verbose mode"
    echo "  --skip-nmb                 Skip NMB tests"
    echo "  --skip-ui                  Skip UI component tests"
    echo "  --skip-module              Skip module system tests"
    echo "  --html                     Generate HTML coverage report"
    echo "  --xml                      Generate XML coverage report"
    echo "  -t, --test-file FILE       Run tests only for a specific file"
    echo ""
    echo "Examples:"
    echo "  $0 --verbose               Run all tests in verbose mode"
    echo "  $0 --skip-ui --skip-module Run only NMB tests"
    echo "  $0 -t tests/test_nmb.py    Run only NMB tests"
}

# Parse arguments
while [[ $# -gt 0 ]]; do
    case "$1" in
        -h|--help)
            print_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=true
            shift
            ;;
        --skip-nmb)
            SKIP_NMB=true
            shift
            ;;
        --skip-ui)
            SKIP_UI=true
            shift
            ;;
        --skip-module)
            SKIP_MODULE=true
            shift
            ;;
        --html)
            HTML_REPORT=true
            shift
            ;;
        --xml)
            XML_REPORT=true
            shift
            ;;
        -t|--test-file)
            TEST_FILE="$2"
            shift 2
            ;;
        *)
            echo "Unknown option: $1"
            print_usage
            exit 1
            ;;
    esac
done

# Build command
CMD="./tests/run_all_tests.py"

if [ "$VERBOSE" = true ]; then
    CMD="$CMD -v"
fi

if [ "$SKIP_NMB" = true ]; then
    CMD="$CMD --skip-nmb"
fi

if [ "$SKIP_UI" = true ]; then
    CMD="$CMD --skip-ui"
fi

if [ "$SKIP_MODULE" = true ]; then
    CMD="$CMD --skip-module"
fi

if [ "$HTML_REPORT" = true ]; then
    CMD="$CMD --html"
fi

if [ "$XML_REPORT" = true ]; then
    CMD="$CMD --xml"
fi

if [ -n "$TEST_FILE" ]; then
    CMD="$CMD -t $TEST_FILE"
fi

# Print and execute the command
echo "Running: $CMD"
exec $CMD 