"""
Concrete provider adapters behind ASAR's typed LLM and search abstractions.
"""

from asar.providers.brave_search import BraveSearchClient
from asar.providers.corpus_search import CorpusSearchClient, build_corpus_search_client
from asar.providers.factory import build_live_llm_client, build_live_search_client
from asar.providers.local_llm import LocalSLMClient, build_local_llm_client
from asar.providers.openai_llm import OpenAILLMClient
from asar.providers.tavily_search import TavilySearchClient

__all__ = [
    "BraveSearchClient",
    "CorpusSearchClient",
    "LocalSLMClient",
    "OpenAILLMClient",
    "TavilySearchClient",
    "build_corpus_search_client",
    "build_live_llm_client",
    "build_live_search_client",
    "build_local_llm_client",
]
