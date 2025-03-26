# BSTI Application Segmentation Fault Fix

## Issue Summary

The BSTI application was crashing with a segmentation fault when starting. The error logs showed:

```
2025-03-26 09:21:30,736 - bsti - INFO - Starting BSTI
2025-03-26 09:21:30,891 - bsti - INFO - Stylesheet loaded from /Users/pentester/Tools/BSTI/src/config/styles.qss
qt.qpa.fonts: Populating font family aliases took 140 ms. Replace uses of missing font family "Segoe UI" with one that exists to avoid this cost. 
[1]    36742 segmentation fault  /usr/local/bin/python3.11 -m src
```

## Root Cause

The issue is related to font handling in the Qt framework. The application is configured to use "Segoe UI" as the primary font, which is not available on macOS. When Qt attempts to use this missing font, it triggers a segmentation fault.

Specifically, in `src/config/config.py`, the font is set to:
```python
FONT_FAMILY = "Segoe UI, Arial, sans-serif"
```

While Qt normally should fall back to the next available font in the list (Arial), there appears to be a bug in the Qt/PyQt implementation that causes a crash instead of properly handling the missing font.

## Fix Applied

The fix involves modifying the font configuration to use a font that is available on the system. For macOS, this means replacing "Segoe UI" with a system font such as "Arial" or "Helvetica".

The following change was made to `src/config/config.py`:
```diff
- FONT_FAMILY = "Segoe UI, Arial, sans-serif"
+ FONT_FAMILY = "Arial, Helvetica, sans-serif"
```

This change ensures that the application will use fonts that are available on macOS, preventing the segmentation fault.

## Testing Approaches

The issue was diagnosed using a custom testing script that performed step-by-step tests:

1. **System Information**: Collected details about the OS, Python version, and Qt version
2. **Dependency Check**: Verified all required Python packages were installed
3. **Font Check**: Checked available fonts on the system
4. **Stylesheet Testing**: Tested loading the stylesheet separately
5. **Component Testing**: Isolated components to find the specific cause of the crash
6. **Font Application Testing**: Tested alternative fonts to verify the fix

The testing confirmed that replacing "Segoe UI" with an available system font resolves the issue.

## Additional Recommendations

1. **Cross-Platform Font Selection**: Consider using a font detection and selection system that checks for font availability at runtime and falls back gracefully.

2. **Error Handling**: Implement more robust error handling around UI initialization to catch and report issues rather than crashing.

3. **Font Configuration by Platform**: Implement platform-specific font configurations:
   ```python
   import platform
   
   if platform.system() == "Windows":
       FONT_FAMILY = "Segoe UI, Arial, sans-serif"
   elif platform.system() == "Darwin":  # macOS
       FONT_FAMILY = "SF Pro Text, Helvetica, Arial, sans-serif"
   else:  # Linux and others
       FONT_FAMILY = "Liberation Sans, Ubuntu, Arial, sans-serif"
   ```

4. **QSS Font References**: Update any references to specific fonts in the QSS stylesheet to use more generic font families or to align with the platform-specific selections.

## Prevention of Future Issues

1. **Cross-Platform Testing**: Implement testing on different platforms (Windows, macOS, Linux) before deploying updates.

2. **Font Resource Bundling**: Consider bundling required fonts with the application to ensure availability across platforms.

3. **Fallback Mechanism**: Implement a font availability check at startup and fallback to known safe fonts if preferred fonts aren't available.

## Supporting Tools

Two utility scripts were created to help diagnose and fix this issue:

1. **bsti_test.py**: A comprehensive diagnostic tool that tests various components of the application to isolate the issue.

2. **fix_bsti_font.py**: A utility to automatically detect available system fonts and apply the appropriate fix to the configuration.

These scripts can be used for diagnosing similar issues in the future or for setting up the application on new systems. 