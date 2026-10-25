import os

from dotenv import load_dotenv
from langchain_groq import ChatGroq

load_dotenv()


def get_llm(temperature: float = 0.0) -> ChatGroq:
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError("GROQ_API_KEY missing. Copy .env.example to .env and fill it in.")
    return ChatGroq(
        model=os.getenv("GROQ_MODEL", "openai/gpt-oss-120b"),
        temperature=temperature,
    )


def get_structured_llm(schema, temperature: float = 0.0):
    """LLM that returns a validated `schema` object.

    Uses Groq's native JSON-schema mode (more reliable than tool-calling on gpt-oss,
    which sometimes answers in plain text and triggers `tool_use_failed`), plus
    automatic retries for the occasional bad generation.
    """
    llm = get_llm(temperature).with_structured_output(schema, method="json_schema")
    return llm.with_retry(stop_after_attempt=3)