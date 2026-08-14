"""
Central configuration for the AI Daily Digest.
Tune what gets pulled in and how much of it here — no need to touch other files
for basic customization.
"""

import os

# ---------------------------------------------------------------------------
# Secrets (set these as GitHub Actions repo secrets, or env vars locally)
# ---------------------------------------------------------------------------
GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY", "")
# Multiple Groq keys for rotation when one hits free-tier rate limits.
# GROQ_API_KEY is the first/primary key; GROQ_API_KEY_2 is an optional second.
GROQ_API_KEYS = [
    k for k in [os.environ.get("GROQ_API_KEY", ""), os.environ.get("GROQ_API_KEY_2", "")]
    if k
]
TELEGRAM_BOT_TOKEN = os.environ.get("TELEGRAM_BOT_TOKEN", "")
TELEGRAM_CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
GITHUB_TOKEN = os.environ.get("GITHUB_TOKEN", "")
REDDIT_CLIENT_ID = os.environ.get("REDDIT_CLIENT_ID", "")
REDDIT_CLIENT_SECRET = os.environ.get("REDDIT_CLIENT_SECRET", "")

# ---------------------------------------------------------------------------
# LLM settings
# ---------------------------------------------------------------------------
GEMINI_MODEL = "gemini-2.0-flash"
GROQ_MODEL = "llama-3.3-70b-versatile"

# ---------------------------------------------------------------------------
# GitHub trending repos (via official Search API, topic-based)
# ---------------------------------------------------------------------------
GITHUB_TOPICS = ["artificial-intelligence", "llm", "ai-agents", "machine-learning"]
GITHUB_MIN_STARS = 50          # ignore tiny/no-signal repos
GITHUB_LOOKBACK_DAYS = 3        # repos pushed to within last N days
GITHUB_MAX_RESULTS_PER_TOPIC = 15

# ---------------------------------------------------------------------------
# arXiv categories to pull recent papers from
# ---------------------------------------------------------------------------
ARXIV_CATEGORIES = ["cs.AI", "cs.CL", "cs.LG", "cs.MA"]
ARXIV_MAX_RESULTS = 40

# ---------------------------------------------------------------------------
# Hacker News (via Algolia search API) — search terms to pull "front page"-ish
# AI-relevant discussion from the last day
# ---------------------------------------------------------------------------
HN_QUERIES = ["AI", "LLM", "agent", "OpenAI", "Anthropic", "GitHub Copilot"]
HN_MIN_POINTS = 30
HN_MAX_RESULTS_PER_QUERY = 15

# ---------------------------------------------------------------------------
# Reddit (public read-only JSON endpoints, no auth needed)
# ---------------------------------------------------------------------------
REDDIT_SUBREDDITS = ["LocalLLaMA", "MachineLearning", "singularity", "artificial"]
REDDIT_MAX_RESULTS_PER_SUB = 10
REDDIT_MIN_UPVOTES = 25

# ---------------------------------------------------------------------------
# RSS/Atom blogs — official company + community sources
# ---------------------------------------------------------------------------
RSS_FEEDS = {
    "OpenAI": "https://openai.com/news/rss.xml",
    "Anthropic": "https://www.anthropic.com/rss.xml",
    "Google DeepMind": "https://deepmind.google/blog/rss.xml",
    "Hugging Face": "https://huggingface.co/blog/feed.xml",
    "Meta AI": "https://ai.meta.com/blog/rss/",
}
RSS_MAX_ITEMS_PER_FEED = 10
RSS_LOOKBACK_HOURS = 30   # slightly over 24h to avoid gaps from cron drift

# ---------------------------------------------------------------------------
# Digest synthesis
# ---------------------------------------------------------------------------
# What the LLM should optimize the final picks for. Edit this freely — it's
# the single biggest lever on digest quality/relevance over time.
CURATION_FOCUS = """
The reader is an AI engineer/developer. They care most about:
- New AI models, product launches, and major capability updates
- Agent frameworks, dev tooling, and anything that helps build AI applications
- GitHub repos and open-source tools that are new or gaining fast traction
- Research papers with practical or notable implications (not just incremental)
- Startup/funding news only when it signals a real shift (new major player, big raise, acquisition)
Skip generic AI hype pieces, opinion pieces without new information, and anything
that's a minor version bump or purely marketing fluff.
"""

MAX_TOP_STORIES = 8
MAX_REPOS = 8
MAX_PAPERS = 6
MAX_QUICK_HITS = 12
