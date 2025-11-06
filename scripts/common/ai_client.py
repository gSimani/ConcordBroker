import os
from typing import Tuple


def get_openai_client_config() -> Tuple[str, str]:
    """
    Determine base_url and api_key for OpenAI-compatible clients.

    Preference order:
      1) Vercel AI Gateway (AI_GATEWAY_API_KEY + base_url https://ai-gateway.vercel.sh/v1)
      2) Direct OpenAI (OPENAI_API_KEY + base_url https://api.openai.com/v1)

    Returns: (base_url, api_key)
    Raises: RuntimeError if no usable key is found.
    """
    gateway_key = os.getenv("AI_GATEWAY_API_KEY")
    if gateway_key:
        return ("https://ai-gateway.vercel.sh/v1", gateway_key)

    openai_key = os.getenv("OPENAI_API_KEY")
    if openai_key:
        return ("https://api.openai.com/v1", openai_key)

    raise RuntimeError("No AI key found. Set AI_GATEWAY_API_KEY or OPENAI_API_KEY.")
