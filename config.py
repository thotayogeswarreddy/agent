"""
RTL Agent Pipeline - Configuration
Uses GOOGLE_API_KEY or GEMINI_API_KEY from environment.
Never hardcode API keys.
"""
import os
from pathlib import Path

# API key from environment (Colab uses userdata.get in notebook)
API_KEY = os.environ.get("GOOGLE_API_KEY") or os.environ.get("GEMINI_API_KEY")

# Model for text generation (Flash-Lite = cheapest, highest free quota)
TEXT_MODEL = "gemini-2.5-flash-lite"
VISION_MODEL = "gemini-2.5-flash-lite"

# Paths - override via RTL_WORK_DIR env; default: ./work (local) or set /content/rtl_agent in Colab
WORK_DIR = Path(os.environ.get("RTL_WORK_DIR", Path(__file__).parent / "work"))
WORK_DIR.mkdir(parents=True, exist_ok=True)

# Agent limits (minimize API calls for billing)
MAX_RETRIES = 3

# Action types for controller (import from spec.schema for full list)
