# Installation Guide

Detailed installation instructions for Trellis CMS.

## System Requirements

- **Python**: 3.9 or higher
- **Operating System**: Linux, macOS, or Windows
- **Disk Space**: ~50MB for Trellis + dependencies
- **RAM**: Minimum 512MB (recommended 1GB+)

## Installing Python

### macOS

Python 3 is usually pre-installed. Check your version:

```bash
python3 --version
```

If you need to install or upgrade:

```bash
# Using Homebrew
brew install python3
```

### Linux (Ubuntu/Debian)

```bash
sudo apt update
sudo apt install python3 python3-pip python3-venv
```

### Windows

Download Python from [python.org](https://www.python.org/downloads/) and run the installer. Make sure to check "Add Python to PATH" during installation.

## Installing Trellis

### Option 1: Install from PyPI (Recommended)

!!! warning "Temporary Additional Steps Required"
    Until qdflask and qdcomments are published to PyPI, install them from GitHub first:

```bash
# Install dependencies from GitHub
pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdflask
pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdcomments

# Install Trellis
pip install trellis-cms
```

!!! info "Future Installation (Once Dependencies Are on PyPI)"
    This will eventually be simplified to just:
    ```bash
    pip install trellis-cms
    ```

### Option 2: Install from Source

For the latest development version:

```bash
git clone https://github.com/almargolis/trellis.git
cd trellis

# Install dependencies from GitHub
pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdflask
pip install git+https://github.com/almargolis/quickdev.git#subdirectory=qdcomments

# Install Trellis
pip install -e .
```

## Verify Installation

Check that Trellis commands are available:

```bash
trellis-init-db --help
trellis-search --help
```

You should see help text for each command.

## Using Virtual Environments (Recommended)

Virtual environments keep Trellis isolated from other Python projects:

```bash
# Create a virtual environment
python3 -m venv trellis-env

# Activate it
source trellis-env/bin/activate  # Linux/macOS
# or
trellis-env\Scripts\activate  # Windows

# Install Trellis
pip install trellis-cms
```

To deactivate:

```bash
deactivate
```

## Next Steps

Continue to [Quick Start](quickstart.md) to set up your first site, or jump to [First Garden](first-garden.md) for a detailed walkthrough.

## Troubleshooting

### "pip: command not found"

On some systems, use `pip3` instead of `pip`:

```bash
pip3 install trellis-cms
```

### "Permission denied"

Use `--user` flag to install for your user only:

```bash
pip install --user trellis-cms
```

Or use a virtual environment (recommended).

### "ModuleNotFoundError"

If Python can't find trellis after installation:

1. Check which Python you're using: `which python3`
2. Check where pip installed packages: `pip show trellis-cms`
3. Make sure they match (same Python version)

### Behind a Proxy

Set environment variables:

```bash
export HTTP_PROXY=http://proxy:port
export HTTPS_PROXY=https://proxy:port
pip install trellis-cms
```
