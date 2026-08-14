# CLAUDE.md

Context for Claude Code (or any agent) working on this repo. Read this before
making changes.

## What this is

A daily AI news digest that runs unattended on GitHub Actions and sends a
curated Telegram message every morning. No server, no database, no paid
dependencies — everything runs on free tiers.

Pipeline: **fetch (4 sources) → dedupe → LLM synthesis (Gemini, Groq fallback)
→ send (Telegram)**. One run = one `python main.py` execution = one message
(or a few chunked messages) delivered.

## File map

```
main.py                     orchestrator — run this to execute a full cycle
src/config.py                ALL tunable settings live here (sources, focus, limits, secrets read from env)
src/sources.py               one fetch_* function per source, all feed into fetch_all()
src/util.py                  dedupe_items() + chunk_text() — pure functions, no I/O
src/llm.py                   prompt construction + Gemini/Groq calls with fallback
src/telegram_sender.py       markdown->Telegram HTML conversion + chunked sending
.github/workflows/daily-digest.yml   cron trigger (00:30 UTC = 6am IST) + workflow_dispatch for manual runs
README.md                    end-user setup instructions (Telegram bot, API keys, secrets)
```

## Core data contract

Every source fetcher in `sources.py` returns a list of dicts shaped exactly
like this — **do not change this shape without updating every consumer**
(`util.dedupe_items`, `llm.build_prompt`):

```python
{
    "title": str,
    "link": str,
    "source": str,     # display name, e.g. "GitHub", "arXiv", "Hacker News"
    "summary": str,    # can be "", used as LLM context, not required for display
    "meta": str,        # short signal string, e.g. "1.2k★ · Python", "450 points"
}
```

Every fetcher must be self-contained and **never raise** — wrap risky calls in
try/except and return `[]` on failure (see existing fetchers for the pattern).
`sources.fetch_all()` already isolates failures per-source, but individual
fetchers should still degrade gracefully (e.g. one topic query failing inside
`fetch_github_trending` shouldn't kill the other topics).

## Secrets / environment variables

Read via `os.environ` in `config.py`, never hardcoded:
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`

In GitHub Actions these come from repo secrets (already wired in the
workflow file). Locally, copy `.env.example` to `.env` and export it. **Never
commit real keys** — `.env` is gitignored.

## Running / testing locally

```bash
pip install -r requirements.txt
export $(cat .env | xargs)      # after filling in .env from .env.example
python main.py                   # full run: fetch -> LLM -> send to Telegram
```

For fast iteration without spamming your Telegram or burning LLM calls, it's
often better to test pieces in isolation, e.g.:

```bash
python -c "from src import sources; print(len(sources.fetch_github_trending()))"
python -c "from src import sources, llm; items = sources.fetch_all(); print(llm.build_prompt(items)[:2000])"
```

`src/util.py` functions are pure and fast — safe to unit test freely.

## Network notes

- `api.github.com` search endpoint uses `GITHUB_TOKEN` (Actions provides this
  automatically, no secret needed) for a higher rate limit (~30 req/min vs
  ~10 unauthenticated) — don't strip that header.
- No Reddit source — Reddit now gates API access behind manual
  registration/approval beyond app creation, dropped to keep setup
  friction-free. See `git log` for a prior OAuth (`client_credentials`)
  implementation if re-adding later.
- arXiv API is polite-use — don't drop the delay/rate discipline if you add
  more categories or increase `ARXIV_MAX_RESULTS` significantly. Also note:
  `requests` double-encodes literal `+` in query params to `%2B` — the
  category filter must be joined with `" OR "` (spaces), not `"+OR+"`, or
  the query silently returns 0 results.

## Design decisions worth knowing before you change things

- **Gemini primary, Groq fallback**: `llm.call_llm()` tries Gemini first,
  catches *any* exception, and falls back to Groq. If you add a third
  provider, keep this same try/except chain pattern.
- **REST calls via `requests`, not SDKs**: intentional, to keep the dependency
  footprint minimal for a GitHub Actions runner. Keep it this way unless
  there's a strong reason to add `google-generativeai` or `groq` SDKs.
- **Dedupe is heuristic, not semantic** (`util.dedupe_items` — word-overlap on
  normalized titles). It's a cheap pre-filter; the LLM prompt also
  instructs the model to dedupe semantically as the real defense. Don't
  over-invest in making the heuristic perfect — improving the LLM prompt or
  adding embeddings (if ever needed) would be a better use of effort.
- **Telegram only, HTML parse mode**: chosen for zero-setup delivery (no
  domain/SMTP verification). `telegram_sender._markdown_to_telegram_html`
  only supports the small tag set Telegram HTML mode allows (`b`, `i`, `a`,
  `code`, `pre`, `u`, `s`) — don't have the LLM prompt request Markdown
  features outside what that converter handles (e.g. tables, nested lists).
- **No persistent state between runs**: each run is stateless — it doesn't
  know what was sent yesterday. This is the most obvious/valuable next
  improvement (see below).

## Known gaps / good next tasks

Roughly in order of value:

1. **Cross-day memory** — store yesterday's sent links (e.g. commit a
   `sent_history.json` back to the repo, or use GitHub Actions cache/artifact)
   and exclude them from today's prompt so persistent trending stories don't
   repeat verbatim.
2. **Per-section token budgeting** — right now all raw items get dumped into
   one prompt; as sources grow this could exceed context or get expensive.
   Consider a cheap keyword/relevance pre-filter before the LLM call, or
   splitting into multiple smaller LLM calls per category.
3. **Manual watchlist** — a way to paste in a link (e.g. a LinkedIn/X post you
   saw) that gets folded into the next digest, since those platforms aren't
   scraped automatically (see README "Known limitations").
4. **Delivery quality** — currently plain chunked Telegram messages. Could
   optionally render a nicer HTML/PDF and send via `sendDocument` alongside
   the chat summary.
5. **Source health monitoring** — if a source silently returns 0 items for
   several days (e.g. an RSS feed URL changed), nothing currently alerts you.
   Worth logging/alerting on that in the Action.
6. **Tests** — there's no test suite yet. `util.py` functions are the easiest
   starting point (pure, no network).

## Style conventions

- Plain, explicit code over cleverness — this repo is meant to be easy to
  read and modify by a solo dev on a free-tier budget, not optimized for
  scale.
- Every new external call should fail soft (try/except, log, continue) unless
  it's the final send step, where a hard failure is fine (you want to know if
  delivery broke).
- Keep tunables in `config.py`, not scattered as magic numbers in logic files.
