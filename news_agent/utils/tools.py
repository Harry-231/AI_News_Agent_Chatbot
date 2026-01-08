# tools.py
import os
import warnings
from dotenv import load_dotenv
from langchain_tavily import TavilySearch

load_dotenv()
os.environ["TAVILY_API_KEY"] = os.getenv("TAVILY_API_KEY", "")

# pydantic warning from langchain_tavily tool model naming; harmless but noisy.
warnings.filterwarnings(
    "ignore",
    message='Field name "(stream|output_schema)" in "TavilyResearch" shadows an attribute.*',
)

search_client = TavilySearch(max_results=6)


async def web_search(query: str) -> list[str]:
    try:
        result = search_client.run(query)
        if isinstance(result, list):
            return [str(r) for r in result]
        return [str(result)]
    except Exception as e:
        return [f"Search error: {e}"]
