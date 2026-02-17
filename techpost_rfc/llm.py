import os
from dotenv import load_dotenv
from langchain_openai import ChatOpenAI
from langchain_core.language_models.chat_models import BaseChatModel

load_dotenv()

def get_llm(model_type: str, model_name: str) -> BaseChatModel:
    """
    Factory function to get the LLM instance.

    Args:
        model_type: "openai" or "ollama" (can be extended).
        model_name: The specific model name (e.g., "gpt-4o", "gpt-3.5-turbo").

    Returns:
        A BaseChatModel instance.
    """
    return ChatOpenAI(
        model="Qwen/Qwen2.5-14B-Instruct-AWQ",
        base_url="http://localhost:8000/v1",
        api_key="dummy",
        temperature=0,
        # 서버 응답 대기 시간 설정
        timeout=120
    )
