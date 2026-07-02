import os
from langchain_nvidia_ai_endpoints import ChatNVIDIA

# FIX: never hardcode API keys in source files. Load from environment
# (populated from .env via python-dotenv or your settings/config module).
api_key = os.environ["NVIDIA_API_KEY"]

client = ChatNVIDIA(
    model="nvidia/nemotron-3-ultra-550b-a55b",
    api_key=api_key,
    temperature=1,
    top_p=0.95,
    max_tokens=16384,
    reasoning_budget=16384,
    chat_template_kwargs={"enable_thinking": True},
)

for chunk in client.stream([{"role": "user", "content": "Hello"}]):
    if chunk.additional_kwargs and "reasoning_content" in chunk.additional_kwargs:
        print(chunk.additional_kwargs["reasoning_content"], end="")
    print(chunk.content, end="")