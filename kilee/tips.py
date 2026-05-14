"""Tips shown at startup to help users discover features."""
import random

TIPS = [
    "/compact  compress context to save tokens",
    "/memory   view persistent cross-session memory",
    "/memory clear  wipe all saved memory",
    "/model deepseek-reasoner  switch to reasoning model",
    "/clear  reset conversation history",
    "Share project info — KiLee will remember it",
    "Paste code directly for KiLee to analyze",
    "Context auto-compresses when it gets long",
    "Ctrl+C interrupts the current task",
    "/tips  show more usage tips",
    "KiLee picks the right tool automatically",
    "/model  check or switch the current model",
    "KiLee can search the web with web_search tool",
    "Use web_fetch to read articles and docs from URLs",
    "Ask KiLee to search for latest news or info",
    "/approval suggest  ask before dangerous operations",
    "/approval auto     auto-approve all operations",
    "/approval never    block dangerous operations",
]

def get_random_tip() -> str:
    return random.choice(TIPS)
