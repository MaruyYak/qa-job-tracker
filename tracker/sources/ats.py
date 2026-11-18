"""Карьерные страницы компаний через публичные API систем найма."""
import time

from ..http import get_json, session

QA_HINT = ("qa", "quality", "test", "tester")


def _looks_qa(title: str) -> bool:
    t = (title or "").lower()
    return any(h in t for h in QA_HINT)


def greenhouse(slug: str) -> list[dict]:
    data = get_json(f"https://boards-api.greenhouse.io/v1/boards/{slug}/jobs", params={"content": "true"})
    out = []
    for j in (data or {}).get("jobs", []):
        if not _looks_qa(j.get("title")):
            continue
        loc = (j.get("location") or {}).get("name", "")
        offices = ", ".join(o.get("name", "") for o in j.get("offices") or [])
        out.append({
            "source": "Greenhouse", "company": j.get("company_name") or slug,
            "title": j.get("title", ""), "location": ", ".join(x for x in (loc, offices) if x),
            "remote": None, "url": j.get("absolute_url"),
            "posted": j.get("first_published") or j.get("updated_at"),
            "description": j.get("content", ""),
        })
    return out


def lever(slug: str, eu: bool = False) -> list[dict]:
    base = "https://api.eu.lever.co" if eu else "https://api.lever.co"
    data = get_json(f"{base}/v0/postings/{slug}", params={"mode": "json"})
    out = []
    for j in data or []:
        if not _looks_qa(j.get("text")):
            continue
        cats = j.get("categories") or {}
        locs = cats.get("allLocations") or [cats.get("location", "")]
        out.append({
            "source": "Lever", "company": slug,
            "title": j.get("text", ""), "location": ", ".join(l for l in locs if l),
            "remote": j.get("workplaceType") == "remote", "url": j.get("hostedUrl"),
            "posted": _ms(j.get("createdAt")),
            "description": (j.get("descriptionPlain") or "") + " " + (j.get("additionalPlain") or "")
                           + " " + " ".join(l.get("content", "") for l in j.get("lists") or []),
        })
    return out


def ashby(slug: str) -> list[dict]:
    data = get_json(f"https://api.ashbyhq.com/posting-api/job-board/{slug}")
    out = []
    for j in (data or {}).get("jobs", []):
        if not j.get("isListed", True) or not _looks_qa(j.get("title")):
            continue
        locs = [j.get("location", "")] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
        out.append({
            "source": "Ashby", "company": slug,
            "title": j.get("title", ""), "location": ", ".join(l for l in locs if l),
            "remote": bool(j.get("isRemote")) or j.get("workplaceType") == "Remote",
            "url": j.get("jobUrl"), "posted": j.get("publishedAt"),
            "description": j.get("descriptionPlain", ""),
        })
    return out


def workable(slug: str) -> list[dict]:
    data = get_json(f"https://apply.workable.com/api/v1/widget/accounts/{slug}", params={"details": "true"})
    out = []
    for j in (data or {}).get("jobs", []):
        if not _looks_qa(j.get("title")):
            continue
        locs = [", ".join(x for x in (l.get("city"), l.get("country")) if x) for l in j.get("locations") or []]
        out.append({
            "source": "Workable", "company": (data or {}).get("name") or slug,
            "title": j.get("title", ""),
            "location": "; ".join(l for l in locs if l) or ", ".join(x for x in (j.get("city"), j.get("country")) if x),
            "remote": bool(j.get("telecommuting")), "url": j.get("url") or j.get("shortlink"),
            "posted": j.get("published_on") or j.get("created_at"),
            "description": j.get("description", ""),
        })
    time.sleep(1.5)  # Workable быстро отвечает 429
    return out


def smartrecruiters(slug: str) -> list[dict]:
    out = []
    data = get_json(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings", params={"limit": 100, "q": "QA"})
    for j in (data or {}).get("content", []):
        if not _looks_qa(j.get("name")):
            continue
        loc = j.get("location") or {}
        detail = get_json(f"https://api.smartrecruiters.com/v1/companies/{slug}/postings/{j['id']}") or {}
        sections = ((detail.get("jobAd") or {}).get("sections") or {})
        desc = " ".join((s or {}).get("text", "") for s in sections.values())
        out.append({
            "source": "SmartRecruiters", "company": (j.get("company") or {}).get("name") or slug,
            "title": j.get("name", ""), "location": loc.get("fullLocation") or ", ".join(
                x for x in (loc.get("city"), loc.get("country")) if x),
            "remote": bool(loc.get("remote")),
            "url": f"https://jobs.smartrecruiters.com/{slug}/{j['id']}",
            "posted": j.get("releasedDate"), "description": desc,
        })
    return out


def _ms(v):
    if not v:
        return None
    import datetime as dt
    return dt.datetime.fromtimestamp(int(v) / 1000, dt.timezone.utc).isoformat()


FETCHERS = {
    "greenhouse": greenhouse,
    "lever": lever,
    "lever_eu": lambda s: lever(s, eu=True),
    "ashby": ashby,
    "workable": workable,
    "smartrecruiters": smartrecruiters,
}
