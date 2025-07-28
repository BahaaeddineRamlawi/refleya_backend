import os
from dotenv import load_dotenv

from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_openai import ChatOpenAI
from langchain_mistralai import ChatMistralAI
from langchain_cohere import ChatCohere

load_dotenv()

async def initialize_openai():
    api_key = os.getenv("OPENAI_API_KEY")
    llm = ChatOpenAI(
        model_name="gpt-4o",
        openai_api_key=api_key,
        temperature=0.7,
    )
    return llm

async def initialize_gemini():
    api_key = os.getenv("GEMINI_API_KEY")
    llm = ChatGoogleGenerativeAI(
        model="gemini-1.5-flash",
        google_api_key=api_key,
        temperature=0.7,
    )
    return llm


async def initialize_mistral():
    api_key = os.getenv("MISTRAL_API_KEY")
    llm = ChatMistralAI(
        api_key=api_key,
        model="mistral-tiny",
        temperature=0.7,
    )
    return llm


async def initialize_mixtral():
    api_key = os.getenv("TOGETHER_API_KEY")
    llm = ChatOpenAI(
        model_name="mistralai/Mixtral-8x7B-Instruct-v0.1",
        openai_api_key=api_key,
        base_url="https://api.together.xyz/v1",
        temperature=0.7,
    )
    return llm


async def initialize_llama():
    api_key = os.getenv("OPENROUTER_API_KEY")
    llm = ChatOpenAI(
        model_name="meta-llama/llama-3-8b-instruct",
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
    )
    return llm


async def initialize_cohere():
    api_key = os.getenv("COHERE_API_KEY")
    llm = ChatCohere(
        model="command-r-plus",
        cohere_api_key=api_key,
        temperature=0.7,
    )
    return llm


async def initialize_deepseek():
    api_key = os.getenv("OPENROUTER_API_KEY")
    llm = ChatOpenAI(
        model_name="deepseek/deepseek-chat-v3-0324:free",
        openai_api_key=api_key,
        base_url="https://openrouter.ai/api/v1",
        temperature=0.7,
    )
    return llm


async def get_model_llm():
    provider = os.getenv("LLM_PROVIDER", "gemini").lower()

    initializer_map = {
        "gemini": initialize_gemini,
        "mistral": initialize_mistral,
        "mixtral": initialize_mixtral,
        "llama 3": initialize_llama,
        "cohere": initialize_cohere,
        "deepseek": initialize_deepseek,
        "openai": initialize_openai,
    }

    initializer = initializer_map.get(provider)
    if initializer is None:
        raise ValueError(f"Unsupported LLM_PROVIDER: {provider}")

    return await initializer()
