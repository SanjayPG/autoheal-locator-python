# Installation Guide

Complete guide for installing AutoHeal Locator Python in various environments.

## Prerequisites

- **Python**: 3.9 or higher
- **pip**: Latest version recommended
- **Selenium**: 4.x (optional, install via extras)
- **Redis**: Optional, for distributed caching

## Basic Installation

### Install from PyPI (When Published)

```bash
# Basic installation
pip install autoheal-locator

# With Selenium support
pip install autoheal-locator[selenium]

# With Redis cache support
pip install autoheal-locator[redis]

# With all optional dependencies
pip install autoheal-locator[all]
```

### Install from Source

```bash
# Clone the repository
git clone https://github.com/SanjayPG/autoheal-locator-python.git
cd autoheal-locator-python

# Install in development mode
pip install -e .

# Or install with extras
pip install -e .[all]
```

## Installation Options

### Development Installation

For contributing or local development:

```bash
# Clone and navigate
git clone https://github.com/SanjayPG/autoheal-locator-python.git
cd autoheal-locator-python

# Install in editable mode with dev dependencies
pip install -e ".[dev]"

# Or use poetry (if available)
poetry install
```

### Production Installation

For production environments:

```bash
# Install with production extras
pip install autoheal-locator[all]

# Or specify exact dependencies
pip install autoheal-locator[selenium,redis]
```

### Minimal Installation

If you only need core functionality:

```bash
# Minimal install (no optional dependencies)
pip install autoheal-locator

# Then manually install what you need
pip install selenium  # If using Selenium
pip install redis     # If using Redis cache
```

## Extras Explained

AutoHeal Locator provides several optional extras:

### `[selenium]`
Installs Selenium WebDriver support:
- `selenium>=4.0.0`
- Required for Selenium integration

```bash
pip install autoheal-locator[selenium]
```

### `[redis]`
Installs Redis caching support:
- `redis>=4.0.0`
- Required for distributed caching

```bash
pip install autoheal-locator[redis]
```

### `[dev]`
Installs development dependencies:
- `pytest>=7.0.0`
- `pytest-asyncio>=0.21.0`
- `pytest-cov>=4.0.0`
- `black>=23.0.0`
- `mypy>=1.0.0`
- `ruff>=0.1.0`

```bash
pip install autoheal-locator[dev]
```

### `[all]`
Installs all optional dependencies:

```bash
pip install autoheal-locator[all]
```

## Verify Installation

After installation, verify it works:

```python
# test_installation.py
from autoheal import AutoHealLocator

print(f"AutoHeal Locator installed successfully!")
print(f"Version: {AutoHealLocator.__version__}")
```

Run the test:
```bash
python test_installation.py
```

## Platform-Specific Instructions

### Windows

```powershell
# Using PowerShell
pip install autoheal-locator[all]

# Set environment variables
$env:GROQ_API_KEY = "gsk-your-api-key"
```

### macOS

```bash
# Using Homebrew Python (recommended)
brew install python@3.11
pip3 install autoheal-locator[all]

# Set environment variables
export GROQ_API_KEY="gsk-your-api-key"
```

### Linux (Ubuntu/Debian)

```bash
# Install Python if needed
sudo apt update
sudo apt install python3.11 python3-pip

# Install AutoHeal
pip3 install autoheal-locator[all]

# Set environment variables
export GROQ_API_KEY="gsk-your-api-key"
```

### Docker

Create a `Dockerfile`:

```dockerfile
FROM python:3.11-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

# Install AutoHeal
RUN pip install --no-cache-dir autoheal-locator[all]

# Set environment variables
ENV GROQ_API_KEY=""

# Copy your test code
COPY . /app
WORKDIR /app

# Run tests
CMD ["pytest", "tests/"]
```

Build and run:
```bash
docker build -t autoheal-tests .
docker run -e GROQ_API_KEY="gsk-your-key" autoheal-tests
```

## Virtual Environment Setup

### Using venv (Recommended)

```bash
# Create virtual environment
python -m venv autoheal-env

# Activate it
# Windows
autoheal-env\Scripts\activate
# macOS/Linux
source autoheal-env/bin/activate

# Install AutoHeal
pip install autoheal-locator[all]
```

### Using Poetry

```bash
# Initialize poetry project
poetry init

# Add AutoHeal
poetry add autoheal-locator

# Add extras
poetry add autoheal-locator[all]

# Install dependencies
poetry install
```

### Using Conda

```bash
# Create conda environment
conda create -n autoheal python=3.11
conda activate autoheal

# Install AutoHeal
pip install autoheal-locator[all]
```

## Dependencies

### Core Dependencies

These are automatically installed:
- `aiohttp>=3.8.0` - Async HTTP client
- `cachetools>=5.0.0` - In-memory caching
- `pydantic>=2.0.0` - Data validation
- `python-dotenv>=1.0.0` - Environment variable management
- `structlog>=23.0.0` - Structured logging

### Optional Dependencies

#### AI Provider SDKs
Different AI providers require different SDKs:

```bash
# OpenAI
pip install openai>=1.0.0

# Anthropic Claude
pip install anthropic>=0.25.0

# Google Gemini
pip install google-generativeai>=0.3.0

# Groq (OpenAI-compatible)
pip install openai>=1.0.0

# Ollama (local)
pip install ollama>=0.1.0
```

AutoHeal will automatically detect and use available providers.

## Configuration Files

### requirements.txt

For pip-based projects:

```txt
# requirements.txt
autoheal-locator[all]>=1.0.0
selenium>=4.0.0
pytest>=7.0.0
pytest-asyncio>=0.21.0
```

Install:
```bash
pip install -r requirements.txt
```

### pyproject.toml

For Poetry projects:

```toml
[tool.poetry]
name = "my-test-project"
version = "1.0.0"
description = "My test automation project"

[tool.poetry.dependencies]
python = "^3.9"
autoheal-locator = {version = "^1.0.0", extras = ["all"]}

[tool.poetry.group.dev.dependencies]
pytest = "^7.0.0"
pytest-asyncio = "^0.21.0"
pytest-cov = "^4.0.0"

[build-system]
requires = ["poetry-core"]
build-backend = "poetry.core.masonry.api"
```

## Troubleshooting Installation

### Common Issues

#### 1. Python Version Too Old

**Error**: `ERROR: Package requires Python '>=3.9'`

**Solution**:
```bash
# Check Python version
python --version

# Upgrade Python
# Windows: Download from python.org
# macOS: brew install python@3.11
# Linux: sudo apt install python3.11
```

#### 2. pip Not Found

**Error**: `bash: pip: command not found`

**Solution**:
```bash
# Use python -m pip instead
python -m pip install autoheal-locator[all]

# Or install pip
python -m ensurepip --upgrade
```

#### 3. Permission Denied

**Error**: `PermissionError: [Errno 13] Permission denied`

**Solution**:
```bash
# Use --user flag
pip install --user autoheal-locator[all]

# Or use virtual environment (recommended)
python -m venv venv
source venv/bin/activate
pip install autoheal-locator[all]
```

#### 4. SSL Certificate Error

**Error**: `SSL: CERTIFICATE_VERIFY_FAILED`

**Solution**:
```bash
# Upgrade certifi
pip install --upgrade certifi

# Or temporary workaround (not recommended)
pip install --trusted-host pypi.org --trusted-host files.pythonhosted.org autoheal-locator[all]
```

#### 5. Dependency Conflicts

**Error**: `ERROR: Cannot install ... because these package versions have conflicting dependencies`

**Solution**:
```bash
# Create fresh virtual environment
python -m venv fresh-env
source fresh-env/bin/activate
pip install autoheal-locator[all]

# Or upgrade pip and setuptools
pip install --upgrade pip setuptools wheel
```

## Upgrade AutoHeal

### Upgrade to Latest Version

```bash
# Upgrade to latest
pip install --upgrade autoheal-locator[all]

# Upgrade to specific version
pip install --upgrade autoheal-locator[all]==1.2.0
```

### Check Installed Version

```python
from autoheal import __version__
print(f"AutoHeal version: {__version__}")
```

Or via pip:
```bash
pip show autoheal-locator
```

## Uninstall

```bash
# Uninstall AutoHeal
pip uninstall autoheal-locator

# Uninstall with cleanup
pip uninstall -y autoheal-locator
pip cache purge
```

## CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/tests.yml
name: Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.11'

    - name: Install dependencies
      run: |
        python -m pip install --upgrade pip
        pip install autoheal-locator[all]
        pip install pytest pytest-cov

    - name: Run tests
      env:
        GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
      run: |
        pytest tests/ -v --cov=autoheal
```

### GitLab CI

```yaml
# .gitlab-ci.yml
test:
  image: python:3.11
  before_script:
    - pip install autoheal-locator[all]
    - pip install pytest pytest-cov
  script:
    - pytest tests/ -v --cov=autoheal
  variables:
    GROQ_API_KEY: $GROQ_API_KEY
```

### Jenkins

```groovy
// Jenkinsfile
pipeline {
    agent any

    stages {
        stage('Install') {
            steps {
                sh 'pip install autoheal-locator[all]'
                sh 'pip install pytest pytest-cov'
            }
        }

        stage('Test') {
            steps {
                withEnv(['GROQ_API_KEY=${GROQ_API_KEY}']) {
                    sh 'pytest tests/ -v --cov=autoheal'
                }
            }
        }
    }
}
```

## Next Steps

- **[Quick Start Guide](quick-start.md)** - Get started quickly
- **[Selenium Usage Guide](selenium-usage-guide.md)** - Selenium integration
- **[AI Configuration](ai-configuration.md)** - Configure AI providers
- **[Groq Setup](../GROQ_SETUP.md)** - FREE Groq API setup

## Support

If you encounter issues during installation:

- **GitHub Issues**: [Report Installation Issues](https://github.com/SanjayPG/autoheal-locator-python/issues)
- **Discussions**: [Ask Questions](https://github.com/SanjayPG/autoheal-locator-python/discussions)
