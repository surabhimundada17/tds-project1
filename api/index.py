from fastapi import FastAPI
import sys
import os

# Add the project root to Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the app
from core_engine.server import app

# Export for Vercel
app = app