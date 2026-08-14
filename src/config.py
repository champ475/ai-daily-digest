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
# Experiment tracking — lets us tag which branch/variant produced a given
# digest, and run locally without hitting the real Telegram chat.
# ---------------------------------------------------------------------------
DIGEST_VERSION = os.environ.get("DIGEST_VERSION", "main")
DRY_RUN = os.environ.get("DRY_RUN", "") == "1"

# ---------------------------------------------------------------------------
# LLM settings
# ---------------------------------------------------------------------------
GEMINI_MODEL = "gemini-flash-latest"
GROQ_MODEL = "llama-3.3-70b-versatile"
# Hard cap on raw items sent into the LLM prompt — with 4 sources fetching
# freely (GitHub alone can return 60), the deduped list can exceed request
# body size limits. Groq's free tier 413'd even at 70 items depending on
# summary lengths, so this is set with real margin, not just under the
# lowest failure point observed.
MAX_ITEMS_FOR_PROMPT = 50
# Items matching these keywords (title/summary, case-insensitive) are
# pushed to the front of the list before the MAX_ITEMS_FOR_PROMPT cap is
# applied, so they survive even when raw fetch volume is high.
PRIORITY_KEYWORDS = ["benchmark", "evaluation", "eval", "agent", "agentic"]

# ---------------------------------------------------------------------------
# GitHub repos (via official Search API). Free-text keyword search
# (matches name+description), NOT GitHub's 'topic:' tag field — many
# high-star, genuinely relevant repos carry no topics or different ones
# (e.g. langchain-ai/deepagents has no 'ai-agents' topic at all), so
# requiring an exact topic match silently excludes them regardless of
# popularity. Two passes per keyword: new repos (created recently, lower
# star bar) and established-but-hot repos (no creation-date limit, high
# star bar, must have been pushed to recently) — see fetch_github_trending.
# ---------------------------------------------------------------------------
GITHUB_KEYWORDS = ["AI agent", "LLM agent", "agentic AI", "MCP server", "AI coding agent"]
# Single bare words (e.g. "agent" alone) are dominated by an enormous pool
# of mega-star repos loosely matching that one word, which pushes genuinely
# relevant mid-tier repos (e.g. a 27k-star repo) far past any usable
# per_page cutoff — confirmed: langchain-ai/deepagents (27,761★) ranked
# outside the top 100 for bare "agent", but rank 88/100 for the two-word
# "AI agent". So the high-star pass reuses the same multi-word keywords,
# just with a much higher per-page limit (see GITHUB_HOT_MAX_RESULTS).
GITHUB_MIN_STARS = 40            # bar for the "new repo" pass
GITHUB_HOT_MIN_STARS = 3000      # bar for the "established/high-star" pass — raised from 1000 to focus on genuinely popular tools; day-to-day momentum is now covered separately by fetch_github_star_trending()
GITHUB_LOOKBACK_DAYS = 7         # new-repo pass: created within last N days
GITHUB_MAX_RESULTS_PER_TOPIC = 10
GITHUB_HOT_MAX_RESULTS = 100     # GitHub's API max per_page — needed for relevant repos to rank within reach
# Raw fetch across 5 keywords x 2 passes x up to 100/page can return 500+
# items after dedup — capped here (split evenly between "new" and
# "high-star") so GitHub can't crowd arXiv/HN/RSS out of the shared
# MAX_ITEMS_FOR_PROMPT cap downstream.
GITHUB_TOTAL_CAP = 40

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
- GitHub repos that are either NEW/fast-growing RIGHT NOW, or established but
  genuinely popular and actively maintained AI/agent-specific tools (high star
  count, recently pushed to) — both are valuable, don't require "launched this
  week" for a repo to qualify. Treat star count (given in the meta field) as a
  real signal of quality/traction throughout — a repo with 5,000 stars is worth
  surfacing even if it's a year old, as long as it's still being actively
  developed and directly relevant to agents/LLM tooling. Some GitHub items are
  tagged "trending" in meta with a stars-gained-today/this-week figure (e.g.
  "+4,475 today") — that's a genuine "gaining popularity right now" signal,
  worth weighing highly. IMPORTANT: trending items are pulled from GitHub's
  overall trending page with no AI-specific filtering, so most will be
  completely unrelated (a browser extension, an OSINT tool, etc.) — apply the
  same AI-engineer relevance judgment to these as to everything else; a
  trending repo that isn't AI/agent/LLM-relevant should simply be skipped,
  its trending status alone doesn't make it belong in this digest.
- Research papers on evaluation, benchmarking, and agent capability measurement
  are especially high-value — new benchmarks, new evals, papers exposing gaps in
  how agents/models are currently measured
- Other research with real practical or notable implications (not just incremental)
- Startup/funding news only when it signals a real shift (new major player, big raise, acquisition)

Deprioritize or skip entirely:
- Generic, non-agent-specific ML infrastructure that's famous mainly for being
  foundational rather than for anything happening with it today (e.g.
  TensorFlow, PyTorch, generic "Transformers" library mentions) — these are
  the "everyone already knows this exists" case, unlike an actively-updated
  agent/tooling repo which is still worth surfacing on its own merits
- Generic AI hype pieces, opinion pieces without new information
- Minor version bumps or purely marketing fluff
- Filler descriptions that just restate what a well-known tool does — if
  covering an established repo, say what's specifically notable about it
  (what it does, why the star count/momentum is deserved), not just "X is
  popular for Y"
"""

MAX_TOP_STORIES = 8
MAX_REPOS = 8
MAX_PAPERS = 6
MAX_QUICK_HITS = 12
