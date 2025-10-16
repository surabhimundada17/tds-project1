import sys
import os
from pathlib import Path

# Add the parent directory to the Python path
current_dir = Path(__file__).parent
parent_dir = current_dir.parent
sys.path.insert(0, str(parent_dir))

# Now import the FastAPI app
from core_engine.server import app

# Vercel expects the app to be available at module level
# This is the entry point for Vercel