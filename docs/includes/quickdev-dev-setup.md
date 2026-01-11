### Working with Quickdev Dependencies

If you're developing features that span both the application and quickdev packages (qdflask, qdcomments, etc.), use editable installations:

```bash
# Clone quickdev repository
git clone https://github.com/almargolis/quickdev.git

# In your application virtual environment
source venv/bin/activate

# Install quickdev packages in editable mode
pip install -e ../quickdev/qdflask
pip install -e ../quickdev/qdcomments

# Changes to quickdev packages take effect immediately
```

**Directory structure:**
```
Projects/
  your-app/
    venv/
    your-app/
  quickdev/
    qdflask/
    qdcomments/
```

**Benefits:**
- Changes in quickdev packages take effect immediately (no reinstall needed)
- Easy to test changes across application and dependencies
- Git workflow works in both repos independently

**Switching back to PyPI versions:**
```bash
pip uninstall qdflask qdcomments
pip install qdflask qdcomments
```
