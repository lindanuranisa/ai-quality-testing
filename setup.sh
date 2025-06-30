#!/bin/bash

# AI Quality Assessment Tool - Setup Script
# Customized for python/src/ structure
# ==========================================

set -e  # Exit on any error

echo "🚀 AI Quality Assessment Tool - Setup Script"
echo "Project Structure: python/src/"
echo "============================================="

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Helper functions
print_step() {
    echo -e "${BLUE}📋 $1${NC}"
}

print_success() {
    echo -e "${GREEN}✅ $1${NC}"
}

print_warning() {
    echo -e "${YELLOW}⚠️ $1${NC}"
}

print_error() {
    echo -e "${RED}❌ $1${NC}"
}

# Check if command exists
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Step 1: Check Python version
print_step "Checking Python installation..."
if command_exists python3; then
    PYTHON_VERSION=$(python3 --version 2>&1 | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
    PYTHON_CMD="python3"
elif command_exists python; then
    PYTHON_VERSION=$(python --version 2>&1 | cut -d' ' -f2)
    print_success "Python $PYTHON_VERSION found"
    PYTHON_CMD="python"
else
    print_error "Python not found. Please install Python 3.8+"
    exit 1
fi

# Step 2: Check system dependencies
print_step "Checking system dependencies..."

# Check Tesseract
if command_exists tesseract; then
    print_success "Tesseract OCR found"
else
    print_warning "Tesseract OCR not found - installing..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get update
        sudo apt-get install -y tesseract-ocr libtesseract-dev
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command_exists brew; then
            brew install tesseract
        else
            print_error "Homebrew not found. Please install Tesseract manually"
        fi
    else
        print_warning "Please install Tesseract OCR manually for your OS"
    fi
fi

# Check Poppler
if command_exists pdftoppm; then
    print_success "Poppler found"
else
    print_warning "Poppler not found - installing..."
    
    if [[ "$OSTYPE" == "linux-gnu"* ]]; then
        sudo apt-get install -y poppler-utils
    elif [[ "$OSTYPE" == "darwin"* ]]; then
        if command_exists brew; then
            brew install poppler
        else
            print_error "Homebrew not found. Please install Poppler manually"
        fi
    else
        print_warning "Please install Poppler manually for your OS"
    fi
fi

# Step 3: Navigate to python/src directory
print_step "Setting up Python environment in python/src/..."
cd python/src

# Step 4: Create virtual environment
if [ -d "venv" ]; then
    print_warning "Virtual environment already exists"
else
    print_step "Creating virtual environment..."
    $PYTHON_CMD -m venv venv
    print_success "Virtual environment created"
fi

# Step 5: Activate virtual environment and install dependencies
print_step "Installing Python dependencies..."
source venv/bin/activate

# Upgrade pip
pip install --upgrade pip

# Create requirements.txt if it doesn't exist
if [ ! -f "requirements.txt" ]; then
    print_step "Creating requirements.txt..."
    cat > requirements.txt << 'EOF'
# AI Quality Assessment Tool - Python Dependencies
anthropic>=0.25.0
python-dotenv>=1.0.0
PyPDF2>=3.0.1
PyMuPDF>=1.23.0
python-pptx>=0.6.21
pdf2image>=1.16.3
pytesseract>=0.3.10
Pillow>=10.0.0
opencv-python>=4.8.0
numpy>=1.24.0
reportlab>=4.0.4
pandas>=2.0.0
requests>=2.31.0
psutil>=5.9.0
EOF
    print_success "Created requirements.txt"
fi

# Install requirements
pip install -r requirements.txt
print_success "Python dependencies installed"

# Step 6: Create .env file
if [ ! -f ".env" ]; then
    print_step "Creating .env template..."
    cat > .env << 'EOF'
# (required)
ANTHROPIC_API_KEY=ask_linda_for_the_claude_api_key
CYPRESS_BASE_URL=alphame_prod_url
API_TOKEN=your_prod_user_api_token
ACCESS_TOKEN=your_prod_user_access_token

# Optional: Other configurations
LOG_LEVEL=INFO

# Model Configuration
CLAUDE_MODEL=claude-3-5-sonnet-20241022


EOF
    print_success "Created .env in your project root"
    print_warning "Please edit .env and add the required"
else
    print_warning ".env already exists"
fi

deactivate

# Step 7: Go back to root and setup Node.js
print_step "Setting up Node.js dependencies..."
cd ../../

# Check Node.js
if command_exists node; then
    NODE_VERSION=$(node --version)
    print_success "Node.js $NODE_VERSION found"
    
    # Install npm dependencies
    if [ -f "package.json" ]; then
        print_step "Installing Node.js dependencies..."
        npm install
        print_success "Node.js dependencies installed"
    else
        print_step "Creating package.json and installing Cypress..."
        npm init -y
        npm install cypress --save-dev
        print_success "Cypress installed"
    fi
else
    print_warning "Node.js not found - Cypress features will be unavailable"
fi

# Step 8: Verify directory structure
print_step "Verifying directory structure..."
mkdir -p data/source_files
mkdir -p data/ai_outputs  
mkdir -p data/extracted
mkdir -p data/reports
mkdir -p downloads
mkdir -p cypress/e2e
mkdir -p cypress/fixtures
print_success "Directory structure verified"

# Final instructions 
echo ""
echo "🎉 Setup completed successfully!"
echo "==============================="
echo ""
echo "📋 Next steps:"
echo "1. Edit .env and add your Claude API key"
echo "2. Edit config.json with your company data (if needed)"
echo "3. Add source files to data/source_files/"
echo "4. Add AI memos to data/ai_outputs/"
echo ""
echo "🚀 To run the tool:"
echo "   cd python/src"
echo "   source venv/bin/activate"
echo "   python main.py"
echo ""
echo "🧪 To run Cypress extraction:"
echo "   npx cypress run --spec \"cypress/e2e/data_extraction.cy.js\""
echo ""
echo "📚 Check README.md for detailed usage instructions"