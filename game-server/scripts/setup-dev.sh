#!/bin/bash

# Planetarion Development Environment Setup
# This script sets up the complete development environment

set -e

echo "🚀 Setting up Planetarion Development Environment"
echo "================================================"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

print_status() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

print_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "Makefile" ] || [ ! -d "src" ]; then
    print_error "Please run this script from the game-server directory"
    exit 1
fi

# Function to check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Check prerequisites
print_status "Checking prerequisites..."

if ! command_exists python3; then
    print_error "Python 3 is required but not installed"
    exit 1
fi

if ! command_exists pip; then
    print_error "pip is required but not installed"
    exit 1
fi

if ! command_exists docker; then
    print_warning "Docker not found - Docker-based tests will not work"
fi

if ! command_exists docker-compose; then
    print_warning "Docker Compose not found - Docker-based tests will not work"
fi

print_success "Prerequisites check complete"

# Setup Python virtual environment
print_status "Setting up Python virtual environment..."

if [ ! -d "src/backend/venv" ]; then
    cd src/backend
    python3 -m venv venv
    print_success "Virtual environment created"
else
    print_success "Virtual environment already exists"
fi

# Activate venv and install dependencies
print_status "Installing Python dependencies..."
cd src/backend
source venv/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
cd ../..

print_success "Python dependencies installed"

# Setup pre-commit hooks
print_status "Setting up pre-commit hooks..."

if command_exists pre-commit; then
    pre-commit install
    pre-commit install --hook-type commit-msg
    print_success "Pre-commit hooks installed"
else
    print_warning "pre-commit not found - install with: pip install pre-commit"
fi

# Setup frontend dependencies (if package.json exists)
if [ -f "src/frontend/package.json" ]; then
    print_status "Setting up frontend dependencies..."
    cd src/frontend
    if command_exists npm; then
        npm install
        print_success "Frontend dependencies installed"
    else
        print_warning "npm not found - frontend dependencies not installed"
    fi
    cd ../..
fi

# Create necessary directories
print_status "Creating necessary directories..."
mkdir -p data logs

# Setup environment files
print_status "Setting up environment files..."

if [ ! -f ".env" ]; then
    cp src/backend/.env .env 2>/dev/null || true
    print_success "Environment file created"
fi

print_success "Development environment setup complete!"
echo ""
echo "🎉 Next steps:"
echo "   1. Run 'make dev-up' to start development containers"
echo "   2. Run 'make unit' to run unit tests"
echo "   3. Visit http://localhost:3000 for the frontend"
echo "   4. Visit http://localhost:5000 for the backend API"
echo ""
echo "📚 Available commands:"
echo "   make help        - Show all available commands"
echo "   make setup       - Complete development setup"
echo "   make quality     - Run code quality checks"
