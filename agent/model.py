import os
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")
#https://openrouter.ai/api/v1"
client = AsyncOpenAI(
    base_url="https://api.openai.com/v1",
    api_key=os.getenv("OPENAI_API_KEY") or "missing-key",
)
