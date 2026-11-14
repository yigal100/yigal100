"""Fetches fresh profile data from GitHub and DEV into data/stats.json, data/articles.json,
and data/calendar.json (last 53 weeks of daily contributions).

Environment variables (all optional):
  PROFILE_TOKEN  classic personal access token (repo + read:user). Lets commit, PR and
                 streak numbers include private work. Falls back to GITHUB_TOKEN.
  GITHUB_TOKEN   the token GitHub Actions provides automatically (public data only).
  DEV_API_KEY    DEV Community API key. Adds total views and DEV followers.

Each source is fetched independently. If one fails, its previous values are kept,
so a flaky API never blanks out part of the profile.
"""

from __future__ import annotations

import datetime
import json
import os
import pathlib
import shutil
import subprocess
import sys
import urllib.parse
import urllib.request
from typing import Annotated

import typer

from profile_console.config import Paths, load_config

PROFILE_QUERY = """
query($login: String!) {
  user(login: $login) {
    createdAt
    followers { totalCount }
    pullRequests { totalCount }
    merged: pullRequests(states: MERGED) { totalCount }
    contributionsCollection { contributionYears }
    repositories(ownerAffiliations: OWNER, isFork: false, privacy: PUBLIC, first: 100) {
      nodes {
        name
        stargazerCount
        forkCount
        languages(first: 20) { edges { size node { name } } }
      }
    }
  }
}"""


def _http_json(url: str, *, user_agent: str, headers: dict | None = None, body: dict | None = None, timeout: int = 30):
    req = urllib.request.Request(
        url,
        data=None if body is None else json.dumps(body).encode(),
        headers={"User-Agent": user_agent, "Accept": "application/json", **(headers or {})},
    )
    if body is not None:
        req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode())


def _graphql(token: str, user_agent: str, query: str, variables: dict | None = None) -> dict:
    res = _http_json(
        "https://api.github.com/graphql",
        user_agent=user_agent,
        headers={"Authorization": f"bearer {token}"},
        body={"query": query, "variables": variables or {}},
    )
    if res.get("errors"):
        raise RuntimeError("GraphQL error: " + "; ".join(e.get("message", "?") for e in res["errors"]))
    return res["data"]


def _load_json(data_dir: pathlib.Path, name: str, default):
    try:
        return json.loads((data_dir / name).read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return default


def _save_json(data_dir: pathlib.Path, name: str, obj) -> None:
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / name).write_text(json.dumps(obj, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")


def _warn(msg: str) -> None:
    # "::warning::" makes the message show up as an annotation on the Actions run page
    print(f"::warning::{msg}" if os.environ.get("GITHUB_ACTIONS") else f"warning: {msg}", file=sys.stderr)


def _years_query(years: list[int]) -> str:
    parts = [
        f"""
    y{y}: contributionsCollection(from: "{y}-01-01T00:00:00Z", to: "{y}-12-31T23:59:59Z") {{
      totalCommitContributions
      contributionCalendar {{ totalContributions weeks {{ contributionDays {{ date contributionCount }} }} }}
    }}"""
        for y in years
    ]
    return "query($login: String!) {\n  user(login: $login) {" + "".join(parts) + "\n  }\n}"


def _streaks(days: dict[datetime.date, int], today: datetime.date) -> tuple[int, int]:
    """Return (current_streak, longest_streak). Current streak may end yesterday if today has 0."""
    dates = sorted(d for d in days if d <= today)
    longest = run = 0
    for d in dates:
        run = run + 1 if days[d] > 0 else 0
        longest = max(longest, run)
    current, d = 0, today
    if days.get(d, 0) == 0:
        d -= datetime.timedelta(days=1)
    while days.get(d, 0) > 0:
        current += 1
        d -= datetime.timedelta(days=1)
    return current, longest


def fetch_github(user: str, token: str, today: datetime.date, user_agent: str) -> dict:
    """Fetch GitHub profile stats and 53-week contribution calendar."""
    u = _graphql(token, user_agent, PROFILE_QUERY, {"login": user})["user"]
    years = sorted(u["contributionsCollection"]["contributionYears"])
    ydata = _graphql(token, user_agent, _years_query(years), {"login": user})["user"] if years else {}

    days: dict[datetime.date, int] = {}
    commits_all = contribs_all = 0
    for y in years:
        c = ydata[f"y{y}"]
        commits_all += c["totalCommitContributions"]
        contribs_all += c["contributionCalendar"]["totalContributions"]
        for week in c["contributionCalendar"]["weeks"]:
            for day in week["contributionDays"]:
                days[datetime.date.fromisoformat(day["date"])] = day["contributionCount"]
    current, longest = _streaks(days, today)
    start = today - datetime.timedelta(weeks=52)
    start -= datetime.timedelta(days=(start.weekday() + 1) % 7)
    calendar = [
        [d.isoformat(), days.get(d, 0)]
        for d in (start + datetime.timedelta(days=i) for i in range((today - start).days + 1))
    ]

    repos = u["repositories"]["nodes"]
    langs: dict[str, int] = {}
    for repo in repos:
        for edge in repo["languages"]["edges"]:
            langs[edge["node"]["name"]] = langs.get(edge["node"]["name"], 0) + edge["size"]
    cur = ydata.get(f"y{today.year}", {})
    return {
        "created_at": u["createdAt"],
        "followers": u["followers"]["totalCount"],
        "prs": u["pullRequests"]["totalCount"],
        "prs_merged": u["merged"]["totalCount"],
        "stars": sum(r["stargazerCount"] for r in repos),
        "forks": sum(r["forkCount"] for r in repos),
        "repo_stars": {r["name"]: r["stargazerCount"] for r in repos},
        "languages": dict(sorted(langs.items(), key=lambda kv: -kv[1])),
        "year": today.year,
        "commits_year": cur.get("totalCommitContributions", 0),
        "commits_all": commits_all,
        "contributions_year": cur.get("contributionCalendar", {}).get("totalContributions", 0),
        "contributions_all": contribs_all,
        "streak_current": current,
        "streak_longest": longest,
        "_calendar": calendar,
    }


def _dev_paged(url: str, user_agent: str, headers: dict | None = None) -> list[dict]:
    out: list[dict] = []
    page = 1
    while True:
        sep = "&" if "?" in url else "?"
        batch = _http_json(f"{url}{sep}per_page=1000&page={page}", user_agent=user_agent, headers=headers)
        if not batch:
            return out
        out.extend(batch)
        if len(batch) < 1000:
            return out
        page += 1


def fetch_dev(dev_user: str, api_key: str | None, user_agent: str) -> tuple[dict, list[dict]]:
    """Fetch DEV Community stats and latest 5 articles."""
    if not dev_user:
        return {}, []
    arts = _dev_paged(f"https://dev.to/api/articles?username={urllib.parse.quote(dev_user)}", user_agent)
    arts.sort(key=lambda a: a["published_at"], reverse=True)
    dev: dict[str, int | None] = {
        "articles": len(arts),
        "reactions": sum(a.get("public_reactions_count", 0) for a in arts),
        "comments": sum(a.get("comments_count", 0) for a in arts),
        "views": None,
        "followers": None,
    }
    if api_key:
        h = {"api-key": api_key, "Accept": "application/vnd.forem.api-v1+json"}
        try:
            mine = _dev_paged("https://dev.to/api/articles/me/published", user_agent, h)
            dev["views"] = sum(a.get("page_views_count", 0) for a in mine)
            if mine:
                arts = sorted(mine, key=lambda a: a["published_at"], reverse=True)
                dev.update(
                    articles=len(arts),
                    reactions=sum(a.get("public_reactions_count", 0) for a in arts),
                    comments=sum(a.get("comments_count", 0) for a in arts),
                )
        except Exception as ex:  # noqa: BLE001 — one missing tile shouldn't fail the run
            _warn(f"DEV views unavailable: {ex}")
        try:
            dev["followers"] = len(_dev_paged("https://dev.to/api/followers/users", user_agent, h))
        except Exception as ex:  # noqa: BLE001
            _warn(f"DEV followers unavailable: {ex}")
    latest = [
        {
            "published_at": a["published_at"],
            "title": a["title"],
            "url": a["url"],
            "reactions": a.get("public_reactions_count", 0),
            "comments": a.get("comments_count", 0),
        }
        for a in arts[:5]
    ]
    return dev, latest


def get_github_token() -> tuple[str | None, bool]:
    """Resolve GitHub token from env vars or gh CLI."""
    token = os.environ.get("PROFILE_TOKEN") or os.environ.get("GITHUB_TOKEN")
    if token:
        return token, bool(os.environ.get("PROFILE_TOKEN"))
    try:
        if shutil.which("gh"):
            res = subprocess.run(["gh", "auth", "token"], capture_output=True, text=True, check=False)
            if res.returncode == 0 and res.stdout.strip():
                return res.stdout.strip(), False
    except Exception:
        pass
    return None, False


def fetch_data(
    data: Annotated[
        pathlib.Path | None,
        typer.Option("--data", help="Folder to write stats.json, articles.json, and calendar.json"),
    ] = None,
    config: Annotated[
        pathlib.Path | None,
        typer.Option("--config", help="Path to profile.toml"),
    ] = None,
) -> None:
    """Fetch latest stats into data/*.json."""
    paths = Paths.resolve(data_dir=data, config_path=config)
    cfg = load_config(paths.config_path)
    user_agent = f"{cfg.profile.github_user}-profile-updater"
    today = datetime.datetime.now(datetime.UTC).date()
    stats = _load_json(paths.data_dir, "stats.json", {})
    articles = _load_json(paths.data_dir, "articles.json", [])
    ok = False

    token, has_profile_token = get_github_token()
    if token:
        try:
            gh = fetch_github(cfg.profile.github_user, token, today, user_agent)
            _save_json(paths.data_dir, "calendar.json", gh.pop("_calendar"))
            stats.update(gh)
            ok = True
            print("github: ok" + (" (with private contributions)" if has_profile_token else " (public only)"))
        except Exception as ex:  # noqa: BLE001
            _warn(f"GitHub fetch failed, keeping previous stats: {ex}")
    else:
        _warn("No PROFILE_TOKEN or GITHUB_TOKEN set, and gh CLI token unavailable; skipping GitHub")

    if cfg.profile.dev_user:
        try:
            dev, latest = fetch_dev(cfg.profile.dev_user, os.environ.get("DEV_API_KEY"), user_agent)
            prev = stats.get("dev") or {}
            stats["dev"] = {k: (v if v is not None else prev.get(k)) for k, v in dev.items()}
            if latest:
                articles = latest
            ok = True
            print("dev: ok" + ("" if os.environ.get("DEV_API_KEY") else " (public only, no DEV_API_KEY)"))
        except Exception as ex:  # noqa: BLE001
            _warn(f"DEV fetch failed, keeping previous values: {ex}")
    else:
        stats["dev"] = {}

    if not ok:
        print("error: every source failed, nothing updated", file=sys.stderr)
        sys.exit(1)
    stats["hackathon_wins"] = cfg.profile.hackathon_wins
    stats["updated"] = today.isoformat()
    _save_json(paths.data_dir, "stats.json", stats)
    _save_json(paths.data_dir, "articles.json", articles)


if __name__ == "__main__":
    typer.run(fetch_data)
