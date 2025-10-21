#!/usr/bin/python3
import sys
import os

# Add your project directory
project_home = '/var/www/tmih_flask'
if project_home not in sys.path:
    sys.path.insert(0, project_home)

# Load environment variables
from dotenv import load_dotenv
load_dotenv(os.path.join(project_home, '.env'))

# Import Flask app
from app import create_app
application = create_app()
