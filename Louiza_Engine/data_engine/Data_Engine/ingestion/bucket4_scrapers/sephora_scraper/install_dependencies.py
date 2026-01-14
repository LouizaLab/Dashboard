#!/usr/bin/env python3
"""Install dependencies for Sephora scraper."""
import subprocess
import sys

def install_requirements():
    """Install packages from requirements.txt."""
    print("Installing dependencies...")
    try:
        subprocess.check_call([
            sys.executable, '-m', 'pip', 'install', '-q', '-r', 'requirements.txt'
        ])
        print("✓ Dependencies installed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"✗ Failed to install dependencies: {e}")
        return False

if __name__ == "__main__":
    install_requirements()




