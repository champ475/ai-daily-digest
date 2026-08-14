import re


def _normalize(title: str) -> str:
    title = title.lower()
    title = re.sub(r"[^a-z0-9\s]", "", title)
    title = re.sub(r"\s+", " ", title).strip()
    return title


def dedupe_items(items, similarity_threshold=0.75):
    """
    Cheap dedupe: normalize titles, then drop items whose normalized title
    shares a high fraction of words with an item already kept. Good enough
    for cross-source duplicates (same story picked up by HN + a blog + Reddit)
    without needing embeddings.
    """
    kept = []
    kept_word_sets = []
    for item in items:
        norm = _normalize(item["title"])
        words = set(norm.split())
        if not words:
            continue
        is_dupe = False
        for kept_words in kept_word_sets:
            if not kept_words:
                continue
            overlap = len(words & kept_words) / max(len(words | kept_words), 1)
            if overlap >= similarity_threshold:
                is_dupe = True
                break
        if not is_dupe:
            kept.append(item)
            kept_word_sets.append(words)
    return kept


def prioritize_keywords(items, keywords):
    """Stable-sort items so ones matching any keyword (in title or summary,
    case-insensitive) come first. Used to make sure high-value categories
    (e.g. evaluation/benchmark papers) survive the MAX_ITEMS_FOR_PROMPT cap
    even when the raw fetch returns more items than fit in the prompt."""
    keywords = [k.lower() for k in keywords]

    def matches(item):
        text = (item.get("title", "") + " " + item.get("summary", "")).lower()
        return any(k in text for k in keywords)

    return sorted(items, key=lambda item: not matches(item))


def cap_with_source_floor(items, max_total, min_per_category, category_fn, priority_keywords):
    """Cap items to max_total while guaranteeing each source category at
    least min_per_category slots (if it has that many items available),
    before filling the rest by keyword priority across everything.

    Without this, a single high-volume source (e.g. GitHub returning 70+
    items where most match the priority keywords) can crowd every other
    source's items out of the cap entirely, even ones that would otherwise
    be included — arXiv/HN/RSS sections came back thin or empty in testing
    once GitHub volume grew.
    """
    by_category = {}
    for item in items:
        by_category.setdefault(category_fn(item), []).append(item)

    guaranteed = []
    remaining_pool = []
    for cat, cat_items in by_category.items():
        cat_items = prioritize_keywords(cat_items, priority_keywords)
        guaranteed.extend(cat_items[:min_per_category])
        remaining_pool.extend(cat_items[min_per_category:])

    guaranteed = prioritize_keywords(guaranteed, priority_keywords)[:max_total]
    slots_left = max_total - len(guaranteed)
    if slots_left > 0:
        remaining_pool = prioritize_keywords(remaining_pool, priority_keywords)
        guaranteed.extend(remaining_pool[:slots_left])
    return guaranteed


def chunk_text(text: str, max_len: int = 4000):
    """Split text into chunks under max_len, breaking on paragraph boundaries
    where possible so Telegram messages don't get cut mid-sentence."""
    if len(text) <= max_len:
        return [text]

    chunks = []
    paragraphs = text.split("\n\n")
    current = ""
    for para in paragraphs:
        candidate = (current + "\n\n" + para) if current else para
        if len(candidate) > max_len:
            if current:
                chunks.append(current)
            if len(para) > max_len:
                # paragraph itself too long, hard-split it
                for i in range(0, len(para), max_len):
                    chunks.append(para[i:i + max_len])
                current = ""
            else:
                current = para
        else:
            current = candidate
    if current:
        chunks.append(current)
    return chunks
