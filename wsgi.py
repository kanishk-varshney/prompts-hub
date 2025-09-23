"""
WSGI Configuration for PythonAnywhere Deployment
"""

import sys
import os
from asgi_wsgi import ASGItoWSGI  # <-- comes from asgi-wsgi package

# Path to your project directory
project_dir = '/home/promptshub/prompts-hub'

if project_dir not in sys.path:
    sys.path.insert(0, project_dir)

# Change working directory
os.chdir(project_dir)

# Import your NiceGUI app
from main import app  # NiceGUI app is ASGI

# Wrap ASGI app for WSGI server
application = ASGItoWSGI(app)
