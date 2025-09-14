#!/usr/bin/env python3
"""
Setup script for Discord Mod Mail Bot
"""

import os
import shutil
from pathlib import Path

def setup_project():
    """Set up the project structure and files"""
    print("Setting up Discord Mod Mail Bot...")

    # Create data directory
    data_dir = Path("data")
    data_dir.mkdir(exist_ok=True)
    print("✓ Created data directory")

    # Create .env file if it doesn't exist
    if not Path(".env").exists():
        if Path(".env.template").exists():
            shutil.copy(".env.template", ".env")
            print("✓ Created .env file from template")
            print("⚠️  Please edit .env file with your Discord bot token and channel ID")
        else:
            print("⚠️  .env.template not found, please create .env manually")

    # Create .gitignore if it doesn't exist
    if not Path(".gitignore").exists():
        gitignore_content = """# Environment variables
.env

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
build/
develop-eggs/
dist/
downloads/
eggs/
.eggs/
lib/
lib64/
parts/
sdist/
var/
wheels/
*.egg-info/
.installed.cfg
*.egg

# Database
data/
*.db
*.sqlite
*.sqlite3

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
"""
        with open(".gitignore", "w") as f:
            f.write(gitignore_content)
        print("✓ Created .gitignore file")

    print("\nSetup complete!")
    print("\nNext steps:")
    print("1. Edit .env file with your Discord bot token and channel ID")
    print("2. Run: python bot.py (for development)")
    print("3. Or run: docker-compose up (for production)")

if __name__ == "__main__":
    setup_project()
