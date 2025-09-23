"""
WSGI Configuration for PythonAnywhere Deployment

This file handles the ASGI-to-WSGI conversion needed for PythonAnywhere.
Copy this file to your PythonAnywhere WSGI configuration.
"""

import sys
import os
from asgiref.wsgi import WsgiToAsgi

# Add your project directory to the Python path
# IMPORTANT: Replace 'yourusername' with your actual PythonAnywhere username
project_dir = '/home/promptshub/prompts-hub'

if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Change to project directory
os.chdir(project_dir)

# Import your NiceGUI app
from main import app

# Convert ASGI to WSGI for PythonAnywhere (use the FastAPI app)
application = WsgiToAsgi(app.fastapi_app)
