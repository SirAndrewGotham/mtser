#!/usr/bin/env python3
# setup.py

import sys
import subprocess
from pathlib import Path

def install_requirements():
    """Install required packages."""
    requirements = [
        'httpx>=0.24.0',
        'tqdm>=4.66.0',
        'moviepy>=1.0.3',
        'numpy>=1.24.0',
        'Pillow>=9.0.0',
        'decorator>=5.0.0'
    ]

    print("Installing dependencies...")
    for package in requirements:
        try:
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])
            print(f"✓ Installed: {package}")
        except subprocess.CalledProcessError:
            print(f"✗ Failed to install: {package}")
            return False
    return True

def create_executable_symlink():
    """Create a symlink/alias for easier execution."""
    script_path = Path(__file__).parent / "mtser.py"

    if sys.platform == "win32":
        # Windows: create a batch file
        bat_path = Path(__file__).parent / "mtser.bat"
        bat_content = f'@echo off\n"{sys.executable}" "{script_path}" %*\n'
        with open(bat_path, 'w') as f:
            f.write(bat_content)
        print(f"Created mtser.bat in current directory")
        print(f"Run with: mtser.bat [options]")
    else:
        # Unix/Linux/macOS: create executable
        import os
        import stat

        # Make the script executable
        os.chmod(script_path, os.stat(script_path).st_mode | stat.S_IEXEC)

        # Create alias instructions
        print("\nTo make mtser available system-wide, add alias to your shell:")
        print(f"  echo 'alias mtser=\"{sys.executable} {script_path}\"' >> ~/.bashrc")
        print("  source ~/.bashrc")
        print("\nOr run directly with: python mtser.py")

def main():
    """Main setup function."""
    print("=" * 60)
    print("MTSer - MTS Link Webinar Downloader Setup")
    print("=" * 60)

    # Check Python version
    if sys.version_info < (3, 7):
        print("✗ Python 3.7 or higher is required")
        sys.exit(1)

    print(f"✓ Python {sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}")

    # Install requirements
    if install_requirements():
        print("\n✓ All dependencies installed successfully!")
    else:
        print("\n⚠ Some dependencies failed to install.")
        print("You can try installing them manually:")
        print("  pip install httpx tqdm moviepy numpy Pillow decorator")

    # Create executable instructions
    print("\n" + "=" * 60)
    create_executable_symlink()
    print("\n" + "=" * 60)

    print("\n✅ Setup completed!")
    print("\nUsage examples:")
    print("  python mtser.py --help")
    print("  python mtser.py --interactive")
    print("  python mtser.py https://my.mts-link.ru/...")

if __name__ == "__main__":
    main()
