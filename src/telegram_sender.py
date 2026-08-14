import re
import requests

from . import config
from .util import chunk_text

TELEGRAM_MAX_LEN = 4096
SAFE_CHUNK_LEN = 3800  # leave margin below Telegram's hard limit


def _markdown_to_telegram_html(text: str) -> str:
    """Convert the LLM's Markdown output into Telegram-safe HTML.
    Telegram HTML mode supports a small tag set: b, i, a, code, pre, u, s.
    """
    # Escape HTML special chars first (except ones we'll reintroduce as tags)
    text = text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")

    # Headings -> bold line (do before link conversion so # chars don't clash)
    text = re.sub(r"^#{1,6}\s*(.+)$", r"<b>\1</b>", text, flags=re.MULTILINE)

    # Markdown links [text](url) -> <a href="url">text</a>
    text = re.sub(r"\[([^\]]+)\]\((https?://[^\s)]+)\)", r'<a href="\2">\1</a>', text)

    # Bold **text** -> <b>text</b>
    text = re.sub(r"\*\*([^*]+)\*\*", r"<b>\1</b>", text)

    # Italic _text_ -> <i>text</i> (e.g. the version stamp line)
    text = re.sub(r"(?<!\w)_([^_\n]+)_(?!\w)", r"<i>\1</i>", text)

    return text.strip()


def send_digest(markdown_text: str):
    if not config.TELEGRAM_BOT_TOKEN or not config.TELEGRAM_CHAT_ID:
        raise RuntimeError("TELEGRAM_BOT_TOKEN or TELEGRAM_CHAT_ID not set")

    html = _markdown_to_telegram_html(markdown_text)
    chunks = chunk_text(html, max_len=SAFE_CHUNK_LEN)

    url = f"https://api.telegram.org/bot{config.TELEGRAM_BOT_TOKEN}/sendMessage"
    for i, chunk in enumerate(chunks):
        resp = requests.post(
            url,
            data={
                "chat_id": config.TELEGRAM_CHAT_ID,
                "text": chunk,
                "parse_mode": "HTML",
                "disable_web_page_preview": True,
            },
            timeout=30,
        )
        if resp.status_code != 200:
            print(f"[telegram] chunk {i+1}/{len(chunks)} failed: {resp.status_code} {resp.text}")
            resp.raise_for_status()
        else:
            print(f"[telegram] sent chunk {i+1}/{len(chunks)}")
