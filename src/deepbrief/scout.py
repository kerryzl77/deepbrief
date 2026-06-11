from __future__ import annotations

import hashlib
import json
import os
import urllib.error
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Any

from deepbrief.config import Config, load_sources
from deepbrief.db import init_database


USER_AGENT = "DeepBrief/0.1 (+https://localhost/deepbrief)"
GITHUB_API_VERSION = "2026-03-10"


@dataclass(frozen=True)
class ScoutItem:
    source_id: str
    url: str
    title: str
    type: str
    published_at: str | None
    summary: str = ""


def main(config: Config) -> None:
    sources = load_sources(config.sources_path)
    conn = init_database(config.state_db, config.migrations_dir)
    discovered_at = datetime.now(timezone.utc).isoformat()
    source_log: list[dict[str, Any]] = []
    items: list[ScoutItem] = []

    for feed in sources.get("feeds", []):
        feed_items, log = fetch_feed_source(feed)
        items.extend(feed_items)
        source_log.append(log)

    arxiv = sources.get("arxiv")
    if isinstance(arxiv, dict):
        arxiv_items, log = fetch_arxiv_source(arxiv)
        items.extend(arxiv_items)
        source_log.append(log)

    for repo in sources.get("repos", []):
        repo_items, log = fetch_repo_source(repo)
        items.extend(repo_items)
        source_log.append(log)

    added = 0
    duplicates = 0
    for item in items:
        item_id = stable_item_id(item.url)
        item_hash = stable_hash({"url": item.url, "title": item.title, "source_id": item.source_id})
        cursor = conn.execute(
            """
            INSERT OR IGNORE INTO items
              (id, source_id, url, title, type, published_at, discovered_at, hash, status)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'new')
            """,
            (
                item_id,
                item.source_id,
                item.url,
                item.title,
                item.type,
                item.published_at,
                discovered_at,
                item_hash,
            ),
        )
        if cursor.rowcount == 1:
            added += 1
        else:
            duplicates += 1
    conn.commit()
    total = int(conn.execute("SELECT COUNT(*) AS n FROM items").fetchone()["n"])
    conn.close()

    result = {
        "status": "ok" if total >= 15 else "insufficient_items",
        "generated_at": discovered_at,
        "state_db": str(config.state_db),
        "fetched_items": len(items),
        "added_count": added,
        "duplicate_count": duplicates,
        "total_items": total,
        "source_log": source_log,
    }
    print(json.dumps(result, indent=2, sort_keys=True))
    if total < 15:
        raise RuntimeError(f"M1 scout requires at least 15 total items; found {total}")


def fetch_feed_source(source: dict[str, Any]) -> tuple[list[ScoutItem], dict[str, Any]]:
    urls = [source["url"], *source.get("alternates", [])]
    errors: list[str] = []
    for index, url in enumerate(urls):
        try:
            payload = http_get(url, headers={})
            items = parse_feed(payload, source)
            if items:
                return items, source_status(source, url, index, len(items), errors)
            errors.append(f"{url}: parsed zero feed entries")
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    page_url = source.get("page_url")
    if page_url:
        try:
            http_get(str(page_url), headers={})
            return [], {
                "id": source.get("id"),
                "kind": "feed",
                "primary_url": source.get("url"),
                "used_url": str(page_url),
                "status": "substituted",
                "items": 0,
                "errors": errors,
                "note": "machine feed unavailable; verified official source page instead",
            }
        except Exception as exc:
            errors.append(f"{page_url}: {exc}")
    return [], {
        "id": source.get("id"),
        "kind": "feed",
        "primary_url": source.get("url"),
        "status": "degraded",
        "items": 0,
        "errors": errors,
    }


def fetch_arxiv_source(source: dict[str, Any]) -> tuple[list[ScoutItem], dict[str, Any]]:
    errors: list[str] = []
    primary_params = {
        "search_query": source["query"],
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": "0",
        "max_results": str(source.get("max_results", 50)),
    }
    fallback_params = {
        "search_query": "cat:cs.CL OR cat:cs.AI",
        "sortBy": "submittedDate",
        "sortOrder": "descending",
        "start": "0",
        "max_results": "25",
    }
    for index, params in enumerate([primary_params, fallback_params]):
        url = f"{source['url']}?{urllib.parse.urlencode(params)}"
        try:
            payload = http_get(url, headers={}, timeout=45)
            entries = parse_feed(payload, source)
            return entries, {
                "id": source.get("id"),
                "kind": "arxiv",
                "primary_url": source.get("url"),
                "used_url": url,
                "status": "verified" if index == 0 else "substituted",
                "items": len(entries),
                "errors": errors,
            }
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    return [], {
        "id": source.get("id"),
        "kind": "arxiv",
        "primary_url": source.get("url"),
        "status": "degraded",
        "items": 0,
        "errors": errors,
    }


def fetch_repo_source(source: dict[str, Any]) -> tuple[list[ScoutItem], dict[str, Any]]:
    url = str(source.get("url") or f"https://api.github.com/repos/{source['owner']}/{source['repo']}/releases")
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": GITHUB_API_VERSION,
    }
    token = os.getenv("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"Bearer {token}"
    try:
        payload = http_get(url, headers=headers)
        releases = json.loads(payload.decode("utf-8"))
        if not isinstance(releases, list):
            raise RuntimeError("GitHub releases response was not a list")
        items = [
            ScoutItem(
                source_id=source["id"],
                url=str(release.get("html_url") or release.get("url")),
                title=str(release.get("name") or release.get("tag_name") or source["name"]),
                type=source.get("type", "repo_release"),
                published_at=release.get("published_at") or release.get("created_at"),
                summary=str(release.get("body") or ""),
            )
            for release in releases[:20]
            if release.get("html_url") or release.get("url")
        ]
        return items, {
            "id": source.get("id"),
            "kind": "repo",
            "primary_url": url,
            "used_url": url,
            "status": "verified",
            "items": len(items),
            "errors": [],
        }
    except Exception as exc:
        return [], {
            "id": source.get("id"),
            "kind": "repo",
            "primary_url": url,
            "status": "degraded",
            "items": 0,
            "errors": [str(exc)],
        }


def http_get(url: str, *, headers: dict[str, str], timeout: int = 20) -> bytes:
    merged = {"User-Agent": USER_AGENT, **headers}
    request = urllib.request.Request(url, headers=merged)
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            status = getattr(response, "status", 200)
            if status >= 400:
                raise RuntimeError(f"HTTP {status}")
            return response.read()
    except urllib.error.HTTPError as exc:
        raise RuntimeError(f"HTTP {exc.code}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(str(exc.reason)) from exc


def parse_feed(payload: bytes, source: dict[str, Any]) -> list[ScoutItem]:
    root = ET.fromstring(payload)
    items: list[ScoutItem] = []
    if root.tag.endswith("rss") or root.find("channel") is not None:
        for node in root.findall("./channel/item")[:30]:
            title = text_or_empty(node.find("title"))
            link = text_or_empty(node.find("link"))
            published = normalize_date(text_or_empty(node.find("pubDate")) or text_or_empty(node.find("date")))
            if title and link:
                items.append(ScoutItem(source["id"], link, title, source.get("type", "article"), published))
        return items

    ns = {"atom": "http://www.w3.org/2005/Atom"}
    for entry in root.findall("atom:entry", ns)[:50] or root.findall(".//{http://www.w3.org/2005/Atom}entry")[:50]:
        title = text_or_empty(entry.find("atom:title", ns))
        link = ""
        for link_node in entry.findall("atom:link", ns):
            rel = link_node.attrib.get("rel", "alternate")
            if rel == "alternate":
                link = link_node.attrib.get("href", "")
                break
        if not link:
            link_node = entry.find("atom:id", ns)
            link = text_or_empty(link_node)
        published = normalize_date(
            text_or_empty(entry.find("atom:published", ns)) or text_or_empty(entry.find("atom:updated", ns))
        )
        if title and link:
            items.append(ScoutItem(source["id"], link, " ".join(title.split()), source.get("type", "article"), published))
    return items


def text_or_empty(node: ET.Element | None) -> str:
    return "" if node is None or node.text is None else node.text.strip()


def normalize_date(value: str) -> str | None:
    if not value:
        return None
    try:
        return parsedate_to_datetime(value).astimezone(timezone.utc).isoformat()
    except (TypeError, ValueError):
        return value


def source_status(
    source: dict[str, Any], url: str, alternate_index: int, item_count: int, errors: list[str]
) -> dict[str, Any]:
    status = "verified" if alternate_index == 0 else "substituted"
    return {
        "id": source.get("id"),
        "kind": "feed",
        "primary_url": source.get("url"),
        "used_url": url,
        "status": status,
        "items": item_count,
        "errors": errors,
    }


def stable_item_id(url: str) -> str:
    return "item_" + hashlib.sha1(url.encode("utf-8")).hexdigest()[:16]


def stable_hash(value: Any) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True).encode("utf-8")).hexdigest()
