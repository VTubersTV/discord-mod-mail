#!/usr/bin/env python3
"""
Python version checker for Discord Mod Mail Bot
"""

import sys

def check_python_version():
    """Check if Python version is compatible"""
    major, minor = sys.version_info[:2]

    print(f"Python version: {major}.{minor}")

    if major == 3 and minor == 13:
        print("⚠️  Python 3.13 detected. Using development version of discord.py.")
        print("   This should work with the development branch of discord.py.")
        return True
    elif major == 3 and minor >= 12:
        print("✅ Python version is compatible!")
        return True
    elif major == 3 and minor < 12:
        print("❌ Python version is too old. Please use Python 3.12 or newer.")
        return False
    else:
        print("❌ Unsupported Python version. Please use Python 3.12 or newer.")
        return False

if __name__ == "__main__":
    if check_python_version():
        print("\nYou can now run the bot with: make run")
    else:
        print("\nPlease install a compatible Python version before running the bot.")
        sys.exit(1)
