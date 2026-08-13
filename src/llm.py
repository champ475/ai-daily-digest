import json
import requests

from . import config

GEMINI_URL = "https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent"
GROQ_URL = "https://api.groq.com/openai/v1/chat/completions"


def _call_gemini(prompt: str) -> str:
    if not config.GEMINI_API_KEY:
        raise RuntimeError("GEMINI_API_KEY not set")
    url = GEMINI_URL.format(model=config.GEMINI_MODEL)
    resp = requests.post(
        url,
        params={"key": config.GEMINI_API_KEY},
        headers={"Content-Type": "application/json"},
        data=json.dumps({
            "contents": [{"parts": [{"text": prompt}]}],
            "generationConfig": {"temperature": 0.4, "maxOutputTokens": 4096},
        }),
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["candidates"][0]["content"]["parts"][0]["text"]


def _call_groq(prompt: str) -> str:
    if not config.GROQ_API_KEY:
        raise RuntimeError("GROQ_API_KEY not set")
    resp = requests.post(
        GROQ_URL,
        headers={
            "Authorization": f"Bearer {config.GROQ_API_KEY}",
            "Content-Type": "application/json",
        },
        data=json.dumps({
            "model": config.GROQ_MODEL,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.4,
            "max_tokens": 4096,
        }),
        timeout=90,
    )
    resp.raise_for_status()
    data = resp.json()
    return data["choices"][0]["message"]["content"]


def call_llm(prompt: str) -> str:
    """Try Gemini first; on any failure (missing key, quota, network, bad
    response) fall back to Groq. Raises only if both fail."""
    try:
        return _call_gemini(prompt)
    except Exception as e:
        print(f"[llm] Gemini failed, falling back to Groq: {e}")
    return _call_groq(prompt)


def _format_items_for_prompt(items):
    lines = []
    for i, item in enumerate(items):
        lines.append(
            f"{i+1}. [{item['source']}] {item['title']}\n"
            f"   Link: {item['link']}\n"
            f"   Meta: {item.get('meta', '')}\n"
            f"   Summary: {item.get('summary', '')[:300]}"
        )
    return "\n".join(lines)


def build_prompt(items):
    items_block = _format_items_for_prompt(items)
    prompt = f"""You are curating a daily AI news digest for an AI engineer/developer.

{config.CURATION_FOCUS}

Below is a raw list of {len(items)} items pulled today from GitHub, arXiv, Hacker News, Reddit, and company blogs. Some are duplicates or low-signal — ignore those. Select and synthesize the best ones into a digest.

RAW ITEMS:
{items_block}

Produce the digest in this exact Markdown structure (omit a section entirely if you have nothing good for it — don't pad with filler):

# AI Daily Digest

## 🔥 Top Stories
(up to {config.MAX_TOP_STORIES} items — the most significant news of the day. For each: a bold title as a link, then 1-2 sentences explaining what happened and why it matters. Not just a headline rewrite — add the "so what".)

## 🛠️ Repos & Tools Worth a Look
(up to {config.MAX_REPOS} items — new or fast-growing open-source tools/repos. Title as link, one line on what it does and why it's notable.)

## 📄 Papers Worth Skimming
(up to {config.MAX_PAPERS} items — research with real practical or notable implications. Title as link, one sentence on the core idea/finding.)

## ⚡ Quick Hits
(up to {config.MAX_QUICK_HITS} items — everything else worth knowing but not worth a full writeup. One line each, title as link.)

Formatting rules:
- Use Markdown links: [Title](url)
- Be concise and information-dense — this is read in a few minutes each morning
- No preamble, no "here is your digest" intro line, start directly with the # heading
- Write in plain, direct language, not marketing-speak
"""
    return prompt


def synthesize_digest(items) -> str:
    prompt = build_prompt(items)
    return call_llm(prompt).strip()
