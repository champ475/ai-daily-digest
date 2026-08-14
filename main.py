"""
Entry point for the AI Daily Digest. Run manually with `python main.py`,
or scheduled via .github/workflows/daily-digest.yml
"""

import sys
import datetime

from src import config, sources, llm, telegram_sender
from src.util import dedupe_items


def main():
    print(f"=== AI Daily Digest run started at {datetime.datetime.utcnow().isoformat()}Z ===")

    raw_items = sources.fetch_all()
    print(f"Total raw items fetched: {len(raw_items)}")

    if not raw_items:
        print("No items fetched from any source — aborting without sending.")
        sys.exit(1)

    deduped = dedupe_items(raw_items)
    print(f"After dedupe: {len(deduped)} items")

    if len(deduped) > config.MAX_ITEMS_FOR_PROMPT:
        print(f"Capping to {config.MAX_ITEMS_FOR_PROMPT} items for LLM prompt (was {len(deduped)})")
        deduped = deduped[:config.MAX_ITEMS_FOR_PROMPT]

    print("Calling LLM for synthesis...")
    digest_markdown = llm.synthesize_digest(deduped)
    print("--- DIGEST PREVIEW ---")
    print(digest_markdown[:1000])
    print("--- END PREVIEW ---")

    print("Sending to Telegram...")
    telegram_sender.send_digest(digest_markdown)

    print("=== Done ===")


if __name__ == "__main__":
    main()
