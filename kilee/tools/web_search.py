import json
import re
from urllib.parse import quote_plus

import httpx

SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_search",
        "description": "Search the web via DuckDuckGo. Use this when you need up-to-date information or answers not in your training data.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Search query",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max results to return (1-10)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def run(query: str, max_results: int = 5) -> str:
    try:
        max_results = max(1, min(10, max_results))
        url = f"https://html.duckduckgo.com/html/?q={quote_plus(query)}"

        resp = httpx.get(
            url,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=15,
        )
        resp.raise_for_status()

        results = _parse_results(resp.text, max_results)
        if not results:
            return "(无搜索结果)"

        output = []
        for i, r in enumerate(results, 1):
            output.append(f"{i}. {r['title']}")
            output.append(f"   URL: {r['url']}")
            output.append(f"   {r['snippet']}")
            output.append("")

        return "\n".join(output).strip()

    except httpx.TimeoutException:
        return "[ERROR] 搜索请求超时"
    except Exception as e:
        return f"[ERROR] 搜索失败: {e}"


def _parse_results(html: str, max_results: int) -> list[dict]:
    results = []
    # DuckDuckGo HTML lite results
    # Find result blocks: class="result" or similar patterns
    blocks = re.split(r'<div[^>]*class="[^"]*result[^"]*"[^>]*>', html)

    for block in blocks[1:]:
        if len(results) >= max_results:
            break

        title_match = re.search(
            r'<a[^>]*class="[^"]*result__a[^"]*"[^>]*>(.*?)</a>', block, re.DOTALL
        )
        snippet_match = re.search(
            r'<a[^>]*class="[^"]*result__snippet[^"]*"[^>]*>(.*?)</a>',
            block,
            re.DOTALL,
        )
        url_match = re.search(r'<a[^>]*href="(https?://[^"]+)"', block)

        if title_match:
            title = re.sub(r"<[^>]+>", "", title_match.group(1)).strip()
            snippet = (
                re.sub(r"<[^>]+>", "", snippet_match.group(1)).strip()
                if snippet_match
                else ""
            )
            url = url_match.group(1) if url_match else ""

            if title:
                results.append({"title": title, "url": url, "snippet": snippet})

    return results
