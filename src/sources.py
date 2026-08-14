"""
Fetchers for each raw content source. Every fetcher returns a list of dicts
with a normalized shape:
    {
        "title": str,
        "link": str,
        "source": str,        # e.g. "GitHub", "arXiv", "HN", "OpenAI Blog"
        "summary": str,       # short description/abstract, may be empty
        "meta": str,          # extra signal e.g. "1.2k stars", "450 points", "120 upvotes"
    }
Every fetcher is defensive: a failure in one source should never crash the
whole run, so each is wrapped in try/except at the call site in main.py.
"""

import time
import datetime
import requests
import feedparser

from . import config

USER_AGENT = "ai-daily-digest/1.0 (personal news aggregator)"
HEADERS = {"User-Agent": USER_AGENT}

GITHUB_HEADERS = dict(HEADERS)
if config.GITHUB_TOKEN:
    GITHUB_HEADERS["Authorization"] = f"Bearer {config.GITHUB_TOKEN}"


def fetch_github_trending():
    items = []
    since_date = (datetime.datetime.utcnow() - datetime.timedelta(days=config.GITHUB_LOOKBACK_DAYS)).strftime("%Y-%m-%d")
    for topic in config.GITHUB_TOPICS:
        query = f"topic:{topic} pushed:>{since_date} stars:>={config.GITHUB_MIN_STARS}"
        url = "https://api.github.com/search/repositories"
        params = {"q": query, "sort": "stars", "order": "desc", "per_page": config.GITHUB_MAX_RESULTS_PER_TOPIC}
        try:
            resp = requests.get(url, params=params, headers=GITHUB_HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            for repo in data.get("items", []):
                items.append({
                    "title": repo["full_name"],
                    "link": repo["html_url"],
                    "source": "GitHub",
                    "summary": repo.get("description") or "",
                    "meta": f"{repo.get('stargazers_count', 0)}★ · {repo.get('language') or 'n/a'}",
                })
        except Exception as e:
            print(f"[github:{topic}] fetch failed: {e}")
        time.sleep(1)  # be polite to unauthenticated rate limits
    return items


def fetch_arxiv():
    items = []
    cat_query = " OR ".join(f"cat:{c}" for c in config.ARXIV_CATEGORIES)
    url = "https://export.arxiv.org/api/query"
    params = {
        "search_query": cat_query,
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "max_results": config.ARXIV_MAX_RESULTS,
    }
    try:
        resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
        resp.raise_for_status()
        feed = feedparser.parse(resp.text)
        for entry in feed.entries:
            items.append({
                "title": entry.title.replace("\n", " ").strip(),
                "link": entry.link,
                "source": "arXiv",
                "summary": entry.summary.replace("\n", " ").strip()[:500],
                "meta": getattr(entry, "arxiv_primary_category", {}).get("term", "") if hasattr(entry, "arxiv_primary_category") else "",
            })
    except Exception as e:
        print(f"[arxiv] fetch failed: {e}")
    return items


def fetch_hackernews():
    items = []
    seen_links = set()
    now_ts = int(time.time())
    since_ts = now_ts - 26 * 3600
    for query in config.HN_QUERIES:
        url = "https://hn.algolia.com/api/v1/search_by_date"
        params = {
            "query": query,
            "tags": "story",
            "numericFilters": f"created_at_i>{since_ts},points>={config.HN_MIN_POINTS}",
            "hitsPerPage": config.HN_MAX_RESULTS_PER_QUERY,
        }
        try:
            resp = requests.get(url, params=params, headers=HEADERS, timeout=20)
            resp.raise_for_status()
            data = resp.json()
            for hit in data.get("hits", []):
                link = hit.get("url") or f"https://news.ycombinator.com/item?id={hit.get('objectID')}"
                if link in seen_links:
                    continue
                seen_links.add(link)
                items.append({
                    "title": hit.get("title", ""),
                    "link": link,
                    "source": "Hacker News",
                    "summary": "",
                    "meta": f"{hit.get('points', 0)} points · {hit.get('num_comments', 0)} comments",
                })
        except Exception as e:
            print(f"[hn:{query}] fetch failed: {e}")
    return items


def fetch_rss():
    items = []
    cutoff = datetime.datetime.utcnow() - datetime.timedelta(hours=config.RSS_LOOKBACK_HOURS)
    for name, feed_url in config.RSS_FEEDS.items():
        try:
            feed = feedparser.parse(feed_url)
            count = 0
            for entry in feed.entries:
                if count >= config.RSS_MAX_ITEMS_PER_FEED:
                    break
                published = None
                if getattr(entry, "published_parsed", None):
                    published = datetime.datetime(*entry.published_parsed[:6])
                elif getattr(entry, "updated_parsed", None):
                    published = datetime.datetime(*entry.updated_parsed[:6])
                if published and published < cutoff:
                    continue
                summary = ""
                if hasattr(entry, "summary"):
                    summary = entry.summary
                items.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": name,
                    "summary": summary[:500],
                    "meta": "",
                })
                count += 1
        except Exception as e:
            print(f"[rss:{name}] fetch failed: {e}")
    return items


def fetch_all():
    """Run every fetcher, print counts for visibility in Action logs, return combined list."""
    all_items = []
    fetchers = [
        ("GitHub", fetch_github_trending),
        ("arXiv", fetch_arxiv),
        ("Hacker News", fetch_hackernews),
        ("RSS Blogs", fetch_rss),
    ]
    for label, fn in fetchers:
        try:
            result = fn()
            print(f"[fetch_all] {label}: {len(result)} items")
            all_items.extend(result)
        except Exception as e:
            print(f"[fetch_all] {label} failed entirely: {e}")
    return all_items
