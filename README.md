# AI Daily Digest

Pulls the day's most relevant AI news — GitHub repos, arXiv papers, Hacker News,
Reddit, and company blogs — dedupes and ranks it with an LLM, and sends you a
curated digest on Telegram every morning at 6am IST. Runs entirely on GitHub
Actions' free tier — no server, no ongoing cost.

## How it works

```
GitHub Actions (cron, 6am IST)
  → fetch: GitHub Search API, arXiv API, HN Algolia API, Reddit JSON, RSS blogs
  → dedupe near-identical stories
  → Gemini Flash (primary) synthesizes + ranks into a digest
      ↳ falls back to Groq (Llama 3.3 70B) if Gemini fails/unavailable
  → send as Telegram message(s)
```

## One-time setup (about 10 minutes)

### 1. Create your Telegram bot
1. Open Telegram, message **@BotFather**
2. Send `/newbot`, follow the prompts, get your **bot token** (looks like `123456:ABC-DEF...`)
3. Start a chat with your new bot (search its username, hit Start) — it needs at least one message from you to be able to message you back
4. Get your **chat ID**: message your bot anything, then visit
   `https://api.telegram.org/bot<YOUR_BOT_TOKEN>/getUpdates` in a browser —
   look for `"chat":{"id": ...}` in the response. That number is your `TELEGRAM_CHAT_ID`.

### 2. Get a free Gemini API key
1. Go to [Google AI Studio](https://aistudio.google.com/apikey)
2. Create an API key (free tier — generous daily quota, plenty for one call/day)

### 3. Get a free Groq API key (fallback)
1. Go to [console.groq.com](https://console.groq.com/keys)
2. Create an API key (free tier)

### 4. Get free Reddit API credentials (read-only, app-only OAuth)
Reddit's public JSON endpoints now require OAuth even for read-only access.
1. Go to [reddit.com/prefs/apps](https://www.reddit.com/prefs/apps), click
   **create another app...**
2. Choose type **script**, fill in any name/redirect URI (e.g.
   `http://localhost`) — not used for this flow
3. After creating, note the **client ID** (string under the app name, looks
   like a short random string) and **secret**

### 5. Push this repo to GitHub
```bash
cd ai-daily-digest
git add -A
git commit -m "Initial commit: AI daily digest"
git remote add origin https://github.com/<your-username>/<your-repo>.git
git push -u origin main
```

### 6. Add secrets to your GitHub repo
Repo → **Settings → Secrets and variables → Actions → New repository secret**.
Add:
- `GEMINI_API_KEY`
- `GROQ_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `TELEGRAM_CHAT_ID`
- `REDDIT_CLIENT_ID`
- `REDDIT_CLIENT_SECRET`

`GITHUB_TOKEN` is provided automatically by Actions — no setup needed, just
used to raise the GitHub Search API rate limit from ~10/min to ~30/min.

### 7. Test it
Go to the **Actions** tab → **AI Daily Digest** workflow → **Run workflow**
(this uses the `workflow_dispatch` trigger, no need to wait for 6am). Check the
logs, and check Telegram for the message.

That's it — it'll now run automatically every day at 6am IST (`30 0 * * *` UTC).

## Customizing

Everything tunable lives in `src/config.py`:
- **Sources**: add/remove GitHub topics, arXiv categories, subreddits, RSS feeds
- **Curation focus**: edit `CURATION_FOCUS` — this is the single biggest lever
  on relevance. Tell it to weight agent tooling higher, ignore certain topics, etc.
- **Section sizes**: `MAX_TOP_STORIES`, `MAX_REPOS`, `MAX_PAPERS`, `MAX_QUICK_HITS`
- **Schedule**: edit the cron expression in `.github/workflows/daily-digest.yml`
  (remember GitHub Actions cron is in UTC)

## Running locally (for testing changes)

```bash
pip install -r requirements.txt
cp .env.example .env   # fill in your keys
export $(cat .env | xargs)   # or use a tool like python-dotenv
python main.py
```

## Known limitations / things to improve later

- **Dedupe is heuristic** (word-overlap on titles), not semantic — the LLM
  synthesis step is the real deduplication line of defense.
- **Reddit/HN/GitHub unauthenticated APIs are rate-limited** — fine for one
  daily run, but don't loop this to run more frequently without adding auth.
- **No LinkedIn/X sources** — those platforms don't offer reliable free APIs
  for this. If you spot something great on either, you can always paste the
  link to me and ask for a one-off deep dive, or we can add a manual watchlist
  feature later.
- **No persistent memory across days** — the digest doesn't currently know
  what it already told you yesterday, so a still-trending story might repeat.
  Easy to add later (store yesterday's links, exclude in the prompt).
