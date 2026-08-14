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

# ---------------------------------------------------------------------------
# LLM settings
# ---------------------------------------------------------------------------
GEMINI_MODEL = "gemini-flash-latest"
GROQ_MODEL = "llama-3.3-70b-versatile"
# Hard cap on raw items sent into the LLM prompt — with 4 sources fetching
# freely (GitHub alone can return 60), the deduped list can exceed request
# body size limits (seen: Groq 413 Payload Too Large at ~113 items). Applied
# after dedupe, right before prompt construction.
MAX_ITEMS_FOR_PROMPT = 70

# ---------------------------------------------------------------------------
# GitHub trending repos (via official Search API, topic-based)
# Filtered on repo CREATION date, not push date — broad topics like
# "artificial-intelligence"/"machine-learning" mostly surface huge
# established repos (they push constantly) and were dropped in favor of
# narrower agent/tooling-focused topics.
# ---------------------------------------------------------------------------
GITHUB_TOPICS = ["ai-agents", "llm-agent", "agentic-ai", "mcp", "llm", "ai-coding-assistant"]
GITHUB_MIN_STARS = 15           # lower bar — new repos haven't had time to accumulate stars yet
GITHUB_LOOKBACK_DAYS = 7         # repos created within last N days
GITHUB_MAX_RESULTS_PER_TOPIC = 12

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
The reader is an AI engineer/developer who wants to know what's NEW today —
not a refresher on tools they already know. They care most about:
- New AI models, product launches, and major capability updates announced today
- New or recently-launched agent frameworks, agentic workflows, agent skills/tools,
  and dev tooling for building AI applications (e.g. a new agent harness, a new
  MCP server, a new coding-agent skill, a new memory/context system for agents)
- GitHub repos that are NEW or fast-growing RIGHT NOW — not repos that are simply
  popular or get pushed to daily. A repo with fewer stars but launched this week is
  more interesting than a 50k-star repo with a routine commit.
- Research papers on evaluation, benchmarking, and agent capability measurement
  are especially high-value — new benchmarks, new evals, papers exposing gaps in
  how agents/models are currently measured
- Other research with real practical or notable implications (not just incremental)
- Startup/funding news only when it signals a real shift (new major player, big raise, acquisition)

Aggressively deprioritize or skip entirely:
- Long-established, widely-known projects (e.g. TensorFlow, PyTorch, LangChain,
  AutoGPT, Streamlit, Transformers) UNLESS there's a genuinely new, notable
  development about them specifically today — being in the raw item list is not
  enough, "X is a popular repo for Y" is not news
- Generic AI hype pieces, opinion pieces without new information
- Minor version bumps or purely marketing fluff
- Filler descriptions that just restate what a well-known tool does
"""

MAX_TOP_STORIES = 8
MAX_REPOS = 8
MAX_PAPERS = 6
MAX_QUICK_HITS = 12
