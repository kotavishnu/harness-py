import os
from pathlib import Path
from openai import AsyncOpenAI
from dotenv import load_dotenv

load_dotenv(Path(__file__).parent.parent / ".env")

_client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=os.getenv("OPENROUTER_API_KEY") or "missing-key",
)


async def call_model(model: str, prompt: str) -> str:
    response = await _client.chat.completions.create(
        model=model,
        messages=[
            {"role": "system", "content": "Answer as briefly as possible. One word or number if you can. No punctuation."},
            {"role": "user", "content": prompt},
        ],
        max_tokens=64,
    )
    return (response.choices[0].message.content or "").strip()
