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
