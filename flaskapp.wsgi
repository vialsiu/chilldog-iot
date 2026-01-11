import sys
import os

# Ensure the project root is on sys.path
PROJECT_ROOT = "/var/www/FlaskApp"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

# Optional: ensure working directory
os.chdir(PROJECT_ROOT)

# Load the Flask app object named "application" from your package
from FlaskApp import application
