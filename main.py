"""
Entry point for the AI Daily Digest. Run manually with `python main.py`,
or scheduled via .github/workflows/daily-digest.yml
"""

import os
import sys
import datetime

from src import config, sources, llm, telegram_sender
from src.util import dedupe_items, cap_with_source_floor


def main():
    print(f"=== AI Daily Digest run started at {datetime.datetime.utcnow().isoformat()}Z (version: {config.DIGEST_VERSION}) ===")

    raw_items = sources.fetch_all()
    print(f"Total raw items fetched: {len(raw_items)}")

    if not raw_items:
        print("No items fetched from any source — aborting without sending.")
        sys.exit(1)

    deduped = dedupe_items(raw_items)
    print(f"After dedupe: {len(deduped)} items")

    if len(deduped) > config.MAX_ITEMS_FOR_PROMPT:
        before = len(deduped)

        def category(item):
            src = item.get("source", "")
            if src in ("GitHub", "arXiv", "Hacker News"):
                return src
            return "RSS"  # RSS items are tagged with their feed name (e.g. "OpenAI"), bucket together

        deduped = cap_with_source_floor(
            deduped, config.MAX_ITEMS_FOR_PROMPT, config.MIN_ITEMS_PER_SOURCE,
            category, config.PRIORITY_KEYWORDS,
        )
        print(f"Capping to {config.MAX_ITEMS_FOR_PROMPT} items for LLM prompt (was {before}, per-source floor + priority keywords applied)")

    print("Calling LLM for synthesis...")
    digest_markdown = llm.synthesize_digest(deduped)
    # Stamp the version/branch right under the title so it's visible in the
    # delivered message — lets multiple experiment runs be told apart later.
    digest_markdown = digest_markdown.replace(
        "# AI Daily Digest", f"# AI Daily Digest\n_Version: {config.DIGEST_VERSION}_", 1
    )
    print("--- DIGEST PREVIEW ---")
    print(digest_markdown[:1000])
    print("--- END PREVIEW ---")

    if config.DRY_RUN:
        out_dir = "dry_run_output"
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, f"digest_{config.DIGEST_VERSION}.md")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(digest_markdown)
        print(f"[dry-run] Skipped Telegram send, wrote digest to {out_path}")
    else:
        print("Sending to Telegram...")
        telegram_sender.send_digest(digest_markdown)

    print("=== Done ===")


if __name__ == "__main__":
    main()
