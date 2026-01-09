#!/bin/bash
# Quick test runner script for jsweb

set -e

echo "================================================"
echo "JsWeb Test Suite"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if virtual environment exists
if [ ! -d "venv" ] && [ ! -d ".venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating one...${NC}"
    python -m venv venv
    source venv/bin/activate
    pip install --upgrade pip
else
    if [ -d ".venv" ]; then
        source .venv/bin/activate
    else
        source venv/bin/activate
    fi
fi

# Install dependencies
echo -e "${YELLOW}Installing dependencies...${NC}"
pip install -e ".[dev]"

# Run tests
echo -e "${YELLOW}Running tests...${NC}"
pytest 

# Check exit code
if [ $? -eq 0 ]; then
    echo -e "${GREEN}Tests passed!${NC}"
    echo -e "${GREEN}Coverage report generated in htmlcov/index.html${NC}"
else
    echo -e "${RED}Tests failed!${NC}"
    exit 1
fi

echo "================================================"
