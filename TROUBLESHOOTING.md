# Metro Universe Strategy Game - Troubleshooting Guide

## Common Launch Issues

### Issue 1: ImportError - Cannot import ResourceProductionSystem

**Error Message:**
```
ImportError: cannot import name 'ResourceProductionSystem' from 'systems.resource_production_system'
```

**Solution:**
This was caused by a circular import issue that has been fixed. Try these steps:

1. **Use the simple launcher:**
   ```
   python main_simple.py
   ```

2. **Or use the batch file:**
   ```
   run_simple.bat
   ```

3. **Test imports separately:**
   ```
   python test_circular.py
   ```

### Issue 2: Python not found

**Error Message:**
```
python : The term 'python' is not recognized...
```

**Solutions:**

1. **Activate virtual environment (if using one):**
   ```
   .venv\Scripts\activate
   python main.py
   ```

2. **Use Python launcher:**
   ```
   py main.py
   ```

3. **Use full Python path:**
   ```
   C:\Python39\python.exe main.py
   ```

### Issue 3: Missing dependencies

**Error Message:**
```
ModuleNotFoundError: No module named 'pygame'
```

**Solution:**
```
pip install pygame numpy
```

Or run the setup script:
```
python setup.py
```

### Issue 4: Performance issues

**Symptoms:**
- Low FPS
- Stuttering
- Slow response

**Solutions:**

1. **Check performance overlay:**
   - Press F3 in-game to see FPS
   - Press F4 to generate performance report

2. **Lower graphics settings:**
   - Disable particle effects
   - Reduce UI scale
   - Lower resolution

3. **Close other applications:**
   - Free up RAM and CPU

### Issue 5: Audio problems

**Symptoms:**
- No sound
- Audio errors

**Solutions:**

1. **Check audio drivers:**
   - Update audio drivers
   - Restart audio service

2. **Disable audio temporarily:**
   - Edit the code to skip audio initialization
   - Or use headphones/different audio device

### Issue 6: Save/Load errors

**Symptoms:**
- Cannot save game
- Save files corrupted
- Load fails

**Solutions:**

1. **Check permissions:**
   - Ensure write access to game directory
   - Run as administrator if needed

2. **Clear save directory:**
   - Delete contents of `saves/` folder
   - Restart game

3. **Check disk space:**
   - Ensure sufficient free space

## Quick Fixes

### Fix 1: Reset to defaults
```
python -c "import shutil; shutil.rmtree('saves', ignore_errors=True); shutil.rmtree('logs', ignore_errors=True)"
```

### Fix 2: Test basic functionality
```
python test_quick.py
```

### Fix 3: Reinstall dependencies
```
pip uninstall pygame numpy
pip install pygame numpy
```

### Fix 4: Use minimal version
If the full game doesn't work, try:
```
python main_simple.py
```

## Debug Information

### Get system info:
```python
import sys
print(f"Python version: {sys.version}")
print(f"Python path: {sys.executable}")

import pygame
print(f"Pygame version: {pygame.version.ver}")
```

### Check imports:
```python
python test_imports.py
```

### Check for circular imports:
```python
python test_circular.py
```

## Advanced Troubleshooting

### Enable debug logging:
Edit `main.py` and change:
```python
logging.basicConfig(level=logging.DEBUG)
```

### Run with verbose output:
```
python -v main.py
```

### Check for file conflicts:
Ensure no files are missing or corrupted by comparing with the original distribution.

## Getting Help

1. **Check the logs:**
   - Look in `logs/` directory for error details
   - Check console output for error messages

2. **Verify installation:**
   - Run `python test_integration.py`
   - Check that all required files are present

3. **System requirements:**
   - Python 3.8 or higher
   - Pygame 2.0 or higher
   - 512 MB RAM minimum
   - 100 MB free disk space

4. **Report issues:**
   - Include error messages
   - Include system information
   - Include steps to reproduce

## Known Issues

### Windows-specific:
- Some antivirus software may flag the game
- Windows Defender may slow down file operations
- Path length limitations on older Windows versions

### Python-specific:
- Virtual environment activation issues
- Multiple Python versions conflicts
- Package installation permissions

### Performance:
- Integrated graphics may have lower performance
- Large save files may slow down loading
- Memory usage increases over long play sessions

## Emergency Recovery

If the game is completely broken:

1. **Delete all generated files:**
   ```
   rmdir /s saves logs
   ```

2. **Reinstall dependencies:**
   ```
   pip install --force-reinstall pygame numpy
   ```

3. **Use the launcher:**
   ```
   python launch.py --check
   ```

4. **Start fresh:**
   - Download a fresh copy of the game
   - Don't copy over old save files initially

---

**Remember:** Most issues are related to Python environment setup or missing dependencies. The game itself is stable once properly configured.