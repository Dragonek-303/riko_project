import os
import requests
from google import genai
from dotenv import load_dotenv

load_dotenv()

SERPAPI_KEY = os.getenv("SERPAPI_KEY")
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

client = genai.Client(api_key=GEMINI_API_KEY)

def search_web(query: str):
    """
    Searches using SerpAPI and then summarizes the results with Gemini.
    Returns a SHORT text, ideal for an LLM.
    """

    if not SERPAPI_KEY:
        return {"status": "error", "message": "Missing SERPAPI_KEY w .env"}

    if not GEMINI_API_KEY:
        return {"status": "error", "message": "Missing GEMINI_API_KEY w .env"}

    try:
        # 1. SerpAPI Search
        serp = requests.get(
            "https://serpapi.com/search",
            params={"q": query, "api_key": SERPAPI_KEY}
        ).json()

        # 2. Summary of results by Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[
                "Answer the question based on these search results. "
                "Convert all units to metric (Celsius, km/h, etc.)."
                "Do not use markdown or other special characters. Plain text only. "
                "Keep your answer brief and to the point:",
                str(serp)
            ]
        )

        summary = response.text.strip()

        return {
            "status": "success",
            "query": query,
            "summary": summary
        }

    except Exception as e:
        return {"status": "error", "message": str(e)}
    
# if __name__ == "__main__":
#     result = search_web("Full specifications for the RTX 6000 Blackwell Pro.")
#     print(result)