# AI Quality Assessment Tool - Quick Setup

**Verifies AI-generated content against source documents using Claude AI**

## 🚀 Quick Start (5 minutes)

### 1. Prerequisites
```bash
# Check you have these installed:
python --version    # Need 3.8+
node --version      # Need 16+
git --version
```

### 2. Clone & Setup
```bash
git clone <repository-url>
cd ai-quality-assessment

# Run automated setup
./setup.sh
```

### 3. Get Claude API Key
1. Get API key from Lindas
2. Edit `python/src/.env`:
```bash
cd python/src
nano .env
# Add: ANTHROPIC_API_KEY=your_actual_key_here
```

### 4. Test It Works
```bash
cd python/src
source venv/bin/activate
python main.py --help
```

## 🎯 Basic Usage

### Run Complete Assessment
```bash
cd python/src
source venv/bin/activate
python main.py
```

### Run Only Python Processing (Skip Web Extraction)
```bash
python main.py --skip-frontend
```

### Create Download Package
```bash
python main.py --download-only
```

## 📁 Key Files

- **Configuration**: `config.json` (root)
- **Python Scripts**: `python/src/*.py`
- **Reports**: `data/reports/` (PDF files)
- **Downloads**: `downloads/` (ZIP packages)

## 🔧 Manual Setup (if setup.sh fails)

```bash
# Python setup
cd python/src
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or: venv\Scripts\activate  # Windows
pip install -r requirements.txt

# Node.js setup
cd ../../
npm install

# Create .env file
cd python/src
echo "ANTHROPIC_API_KEY=your_key_here" > .env
```

## 🆘 Common Issues

**Python not found**: Install Python 3.8+
**Permission denied**: Run `chmod +x setup.sh`
**API errors**: Check your API key in `python/src/.env`
**File not found**: Make sure you're in the right directory

## 📊 Current Test Companies

- Algorithmics
- Brightband  
- PepperMoney
- PragmaClin

---
**⚡ TL;DR**: `git clone` → `./setup.sh` → get API key → `cd python/src && python main.py`