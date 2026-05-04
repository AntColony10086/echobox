"""OpenAI-compatible chat model factory.

Default uses DashScope (qwen-plus). Override via:
- ECHOBOX_APP_LLM_BASE_URL  (e.g. OpenAI, DeepSeek, local vLLM)
- ECHOBOX_APP_LLM_MODEL
- ECHOBOX_APP_LLM_API_KEY
"""

from langchain_openai import ChatOpenAI

from echobox_app.config import AppSettings


def build_chat_model(settings: AppSettings) -> ChatOpenAI:
    return ChatOpenAI(
        model=settings.llm_model,
        api_key=settings.llm_api_key,
        base_url=settings.llm_base_url,
        timeout=settings.llm_timeout_s,
        max_retries=1,
    )
