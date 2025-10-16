# Vercel serverless function entry point
from core_engine.server import app

# This is required for Vercel
handler = app