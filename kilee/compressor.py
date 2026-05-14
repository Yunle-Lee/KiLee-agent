"""上下文压缩 — 对话过长时自动摘要中间轮次，保留头尾"""
from openai import OpenAI
from kilee import config

# token 粗估：1 token ≈ 4 字符
def _estimate_tokens(messages: list) -> int:
    total = 0
    for m in messages:
        content = m.get("content") or ""
        if isinstance(content, list):
            content = " ".join(c.get("text", "") for c in content if isinstance(c, dict))
        total += len(str(content)) // 4
    return total

COMPRESS_THRESHOLD = 6000   # token 数超过此值触发压缩
KEEP_HEAD = 1               # 保留开头几条（system prompt）
KEEP_TAIL = 6               # 保留最近几条

SUMMARY_PROMPT = """你是一个对话摘要助手。将以下对话历史压缩为简洁摘要。

要求：
1. 保留所有已完成的任务和结论
2. 记录未完成的工作（## 进行中的任务）
3. 记录重要的文件路径、变量名、决策
4. 不要回答对话中的问题，只做摘要

输出格式：
## 已完成
- ...

## 进行中的任务
- ...

## 重要信息
- ...
"""

def maybe_compress(messages: list, console=None) -> tuple[list, bool]:
    """如果超过阈值则压缩，返回 (新messages, 是否压缩了)"""
    if _estimate_tokens(messages) < COMPRESS_THRESHOLD:
        return messages, False

    head = messages[:KEEP_HEAD]
    tail = messages[-KEEP_TAIL:]
    middle = messages[KEEP_HEAD:-KEEP_TAIL]

    if not middle:
        return messages, False

    if console:
        console.print("[dim yellow]⟳ 上下文过长，正在压缩...[/dim yellow]")

    # 用便宜模型做摘要
    cfg = config.load()
    client = OpenAI(api_key=cfg.get("api_key", ""), base_url=cfg["base_url"])

    middle_text = "\n".join(
        f"[{m['role']}]: {m.get('content', '')[:500]}"
        for m in middle
        if m.get("role") in ("user", "assistant") and m.get("content")
    )

    try:
        resp = client.chat.completions.create(
            model="deepseek-chat",
            messages=[
                {"role": "system", "content": SUMMARY_PROMPT},
                {"role": "user", "content": middle_text},
            ],
            max_tokens=1500,
        )
        summary = resp.choices[0].message.content
    except Exception as e:
        return messages, False

    summary_msg = {
        "role": "system",
        "content": (
            "[CONTEXT COMPACTION] 以下是之前对话的摘要，作为背景参考，"
            "不要重复执行其中已完成的任务：\n\n" + summary
        ),
    }

    new_messages = head + [summary_msg] + tail
    if console:
        saved = _estimate_tokens(messages) - _estimate_tokens(new_messages)
        console.print(f"[dim green]✓ 压缩完成，节省约 {saved} tokens[/dim green]")

    return new_messages, True
