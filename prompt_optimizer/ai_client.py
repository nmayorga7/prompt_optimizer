"""
AI client functions for interacting with OpenAI.
"""

import os
from typing import Dict, List, Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

# Global client instance
_client: Optional[OpenAI] = None


def get_client() -> OpenAI:
    """Get or create the OpenAI client instance."""
    global _client
    if _client is None:
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY not found in environment variables")
        _client = OpenAI(api_key=api_key)
    return _client


def chat_completion(
    model: str, messages: List[Dict[str, str]], temperature: float = 0.7
) -> str:
    """Make a chat completion request to the AI model."""
    client = get_client()
    response = client.chat.completions.create(
        model=model, messages=messages, temperature=temperature
    )
    return response.choices[0].message.content
