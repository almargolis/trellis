# ============================================================================
# File: setup.py - Initial Setup Script
# Run this first to set up the new Flask project
# ============================================================================

import os
import secrets
from pathlib import Path
from werkzeug.security import generate_password_hash

def create_directory_structure():
    """Create the Flask project directory structure"""
    base_dir = Path('/Users/almargolis/projects/tmih_flask')
    
    directories = [
        'app',
        'app/templates',
        'app/static',
        'app/static/css',
        'app/static/js',
        'app/static/images',
        'app/utils',
        'content',
        'migrations'
    ]
    
    for directory in directories:
        dir_path = base_dir / directory
        dir_path.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created {directory}")

def create_env_file():
    """Create .env file with generated secrets"""
    base_dir = Path('/Users/almargolis/projects/tmih_flask')
    env_file = base_dir / '.env'
    
    if env_file.exists():
        response = input(".env file already exists. Overwrite? (y/n): ")
        if response.lower() != 'y':
            print("Skipping .env creation")
            return
    
    secret_key = secrets.token_hex(32)
    
    print("\n=== Admin Account Setup ===")
    username = input("Admin username (default: admin): ").strip() or "admin"
    password = input("Admin password: ").strip()
    
    if not password:
        print("Password cannot be empty!")
        return
    
    password_hash = generate_password_hash(password)
    
    env_content = f"""# Flask Configuration
SECRET_KEY={secret_key}
FLASK_ENV=development

# Admin Credentials
ADMIN_USERNAME={username}
ADMIN_PASSWORD_HASH={password_hash}

# Git Configuration
GITLAB_REPO_PATH=/Users/almargolis/projects/tmih_flask
"""
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"\n✓ Created .env file")
    print(f"  Username: {username}")
    print("  Password: [saved securely]")

def create_gitignore():
    """Create .gitignore file"""
    base_dir = Path('/Users/almargolis/projects/tmih_flask')
    gitignore_file = base_dir / '.gitignore'
    
    gitignore_content = """# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/

# Flask
instance/
.webassets-cache

# Environment variables
.env
.env.local

# IDEs
.vscode/
.idea/
*.swp
*.swo
*~

# OS
.DS_Store
Thumbs.db

# Databases
*.db
*.sqlite
*.sqlite3

# Logs
*.log
"""
    
    with open(gitignore_file, 'w') as f:
        f.write(gitignore_content)
    
    print("✓ Created .gitignore")

def initialize_git():
    """Initialize git and link to GitLab"""
    base_dir = Path('/Users/almargolis/projects/tmih_flask')
    os.chdir(base_dir)
    
    if not (base_dir / '.git').exists():
        os.system('git init')
        print("✓ Initialized git repository")
    
    # Get the remote from the Hugo repo
    hugo_dir = Path('/Users/almargolis/projects/tmih_hugo')
    if hugo_dir.exists():
        os.chdir(hugo_dir)
        result = os.popen('git remote get-url origin').read().strip()
        if result:
            os.chdir(base_dir)
            os.system(f'git remote add origin {result}')
            print(f"✓ Added GitLab remote: {result}")
            print("  Note: You may want to use a different branch for the Flask version")
            print("  Suggestion: git checkout -b flask-migration")

def main():
    print("=== Flask Blog Setup ===\n")
    
    print("Step 1: Creating directory structure...")
    create_directory_structure()
    
    print("\nStep 2: Creating .gitignore...")
    create_gitignore()
    
    print("\nStep 3: Creating .env file with secrets...")
    create_env_file()
    
    print("\nStep 4: Initializing git...")
    initialize_git()
    
    print("\n=== Setup Complete! ===")
    print("\nNext steps:")
    print("1. Run the migration script: python migrate_content.py")
    print("2. Copy the code files from the artifacts to the appropriate locations")
    print("3. Install dependencies: pip install -r requirements.txt")
    print("4. Extract logo colors and update colors.css")
    print("5. Run the application: python run.py")
    print("6. Access the site at http://localhost:5000")

if __name__ == '__main__':
    main()
    