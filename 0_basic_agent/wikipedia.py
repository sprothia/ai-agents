import requests

def wikipedia_summary(topic: str) -> str:
    try:
        url = "https://en.wikipedia.org/api/rest_v1/page/summary/" + requests.utils.quote(topic)
        response = requests.get(url, timeout=10, headers={"User-Agent": "basic-agent/1.0"})
        if response.status_code == 404:
            return f"No Wikipedia article found for '{topic}'."
        response.raise_for_status()
        data = response.json()
        title = data.get("title", topic)
        summary = data.get("extract", "No summary available.")
        page_url = data.get("content_urls", {}).get("desktop", {}).get("page", "")
        return f"{title}\n\n{summary}\n\nSource: {page_url}"
    except requests.Timeout:
        return "Wikipedia request timed out."
    except Exception as e:
        return f"Error fetching Wikipedia article: {e}"
