"""Агрегаторы и доски удалённой работы."""
import datetime as dt
import time
import xml.etree.ElementTree as ET

from ..http import get, get_json

QUERIES = ["QA", "manual QA", "QA engineer", "software tester", "quality assurance"]


def arbeitnow() -> list[dict]:
    out = []
    for page in range(1, 6):
        data = get_json("https://www.arbeitnow.com/api/job-board-api", params={"page": page})
        if not data or not data.get("data"):
            break
        for j in data["data"]:
            tags = " ".join(j.get("tags") or [])
            out.append({
                "source": "Arbeitnow", "company": j.get("company_name", ""),
                "title": j.get("title", ""), "location": j.get("location", ""),
                "remote": bool(j.get("remote")), "url": j.get("url"),
                "posted": _ts(j.get("created_at")),
                "description": (j.get("description") or "") + " " + tags,
            })
    return out


def remotive() -> list[dict]:
    out = {}
    for q in ("qa", "tester", "quality assurance"):
        data = get_json("https://remotive.com/api/remote-jobs", params={"search": q})
        for j in (data or {}).get("jobs", []):
            out[j["id"]] = {
                "source": "Remotive", "company": j.get("company_name", ""),
                "title": j.get("title", ""), "location": j.get("candidate_required_location", ""),
                "remote": True, "url": j.get("url"), "posted": j.get("publication_date"),
                "description": j.get("description", ""),
            }
    return list(out.values())


def remoteok() -> list[dict]:
    data = get_json("https://remoteok.com/api") or []
    out = []
    for j in data[1:]:
        out.append({
            "source": "RemoteOK", "company": j.get("company", ""),
            "title": j.get("position", ""), "location": j.get("location", ""),
            "remote": True, "url": j.get("url"), "posted": j.get("date"),
            "description": j.get("description", "") + " " + " ".join(j.get("tags") or []),
        })
    return out


def himalayas() -> list[dict]:
    out = {}
    for q in ("QA engineer", "manual QA", "software tester", "quality assurance"):
        for page in range(1, 4):
            time.sleep(3)  # Himalayas отвечает 429 при частых запросах
            data = get_json("https://himalayas.app/jobs/api/search", params={"q": q, "page": page})
            jobs = (data or {}).get("jobs") or []
            for j in jobs:
                restr = ", ".join(j.get("locationRestrictions") or []) or "Worldwide"
                out[j.get("guid")] = {
                    "source": "Himalayas", "company": j.get("companyName", ""),
                    "title": j.get("title", ""), "location": restr,
                    "remote": True, "url": j.get("applicationLink") or j.get("guid"),
                    "posted": _ts(j.get("pubDate")), "description": j.get("description", ""),
                }
            if len(jobs) < 20:
                break
    return list(out.values())


def jobicy() -> list[dict]:
    out = {}
    for tag in ("qa", "tester", "quality assurance"):
        data = get_json("https://jobicy.com/api/v2/remote-jobs", params={"count": 100, "tag": tag})
        for j in (data or {}).get("jobs", []):
            out[j["id"]] = {
                "source": "Jobicy", "company": j.get("companyName", ""),
                "title": j.get("jobTitle", ""), "location": j.get("jobGeo", ""),
                "remote": True, "url": j.get("url"), "posted": j.get("pubDate"),
                "description": j.get("jobDescription", ""),
            }
    return list(out.values())


def weworkremotely() -> list[dict]:
    out = []
    for feed in ("remote-jobs.rss",):
        r = get(f"https://weworkremotely.com/{feed}")
        if r is None:
            continue
        try:
            root = ET.fromstring(r.content)
        except ET.ParseError:
            continue
        for item in root.iter("item"):
            title = item.findtext("title") or ""
            company, _, pos = title.partition(":")
            out.append({
                "source": "WeWorkRemotely", "company": company.strip() if pos else "",
                "title": (pos or title).strip(), "location": item.findtext("region") or "",
                "remote": True, "url": item.findtext("link"), "posted": item.findtext("pubDate"),
                "description": item.findtext("description") or "",
            })
    return out


def _ts(v):
    if v in (None, ""):
        return None
    try:
        return dt.datetime.fromtimestamp(int(v), dt.timezone.utc).isoformat()
    except (TypeError, ValueError):
        return str(v)


FETCHERS = {
    "arbeitnow": arbeitnow,
    "remotive": remotive,
    "remoteok": remoteok,
    "himalayas": himalayas,
    "jobicy": jobicy,
    "weworkremotely": weworkremotely,
}
