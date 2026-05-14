import re

import httpx

SCHEMA = {
    "type": "function",
    "function": {
        "name": "web_fetch",
        "description": "Fetch and extract text content from a URL. Use this to read articles, documentation, or any web page.",
        "parameters": {
            "type": "object",
            "properties": {
                "url": {
                    "type": "string",
                    "description": "The URL to fetch",
                },
                "max_chars": {
                    "type": "integer",
                    "description": "Max characters to return (default 5000)",
                    "default": 5000,
                },
            },
            "required": ["url"],
        },
    },
}

USER_AGENT = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"


def run(url: str, max_chars: int = 5000) -> str:
    if not url.startswith(("http://", "https://")):
        url = "https://" + url

    try:
        resp = httpx.get(
            url,
            headers={"User-Agent": USER_AGENT},
            follow_redirects=True,
            timeout=20,
        )
        resp.raise_for_status()

        text = _extract_text(resp.text)
        text = _clean_text(text)

        if len(text) > max_chars:
            text = text[:max_chars] + f"\n\n... (truncated, full length: {len(text)} chars)"

        return text.strip() or "(页面无文本内容)"

    except httpx.TimeoutException:
        return "[ERROR] 请求超时"
    except httpx.HTTPStatusError as e:
        return f"[ERROR] HTTP {e.response.status_code}"
    except Exception as e:
        return f"[ERROR] 获取失败: {e}"


def _extract_text(html: str) -> str:
    text = html

    text = re.sub(r"<script[^>]*>.*?</script>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<nav[^>]*>.*?</nav>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<footer[^>]*>.*?</footer>", "", text, flags=re.DOTALL | re.IGNORECASE)

    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</p>", "\n\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?li>", "\n", text, flags=re.IGNORECASE)
    text = re.sub(r"</?h[1-6]>", "\n\n", text, flags=re.IGNORECASE)

    text = re.sub(r"<[^>]+>", "", text)

    return text


def _clean_text(text: str) -> str:
    text = re.sub(r"\n{3,}", "\n\n", text)
    text = re.sub(r" {2,}", " ", text)
    lines = [line.strip() for line in text.splitlines()]
    text = "\n".join(line for line in lines if line)
    return text.strip()
