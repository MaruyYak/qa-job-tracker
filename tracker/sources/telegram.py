"""Публичные Telegram-каналы с вакансиями (через веб-превью t.me/s/<канал>)."""
import datetime as dt
import html
import re

from ..http import get

CHANNELS = ["jobforqa", "qa_work", "relocateme", "itjobsgeorgia"]
MAX_AGE_DAYS = 21

MSG_RE = re.compile(
    r'data-post="([^"]+)".*?(?:tgme_widget_message_text[^>]*>(.*?)</div>).*?datetime="([^"]+)"', re.S
)
QA_LINE = re.compile(r"\b(qa|tester|тестировщик|testing|quality assurance|test engineer)\b", re.I)


def _text(fragment: str) -> str:
    s = re.sub(r"<br\s*/?>", "\n", fragment)
    s = re.sub(r"<[^>]+>", " ", s)
    return html.unescape(s)


def channel(name: str) -> list[dict]:
    out = []
    url = f"https://t.me/s/{name}"
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=MAX_AGE_DAYS)
    for _ in range(3):  # 3 страницы по ~20 постов
        r = get(url)
        if r is None:
            break
        page = r.text
        found = MSG_RE.findall(page)
        if not found:
            break
        for post, body, when in found:
            try:
                posted = dt.datetime.fromisoformat(when)
            except ValueError:
                continue
            if posted < cutoff:
                continue
            text = _text(body)
            lines = [l.strip(" •-–—*#") for l in text.splitlines() if l.strip()]
            title = next((l for l in lines if QA_LINE.search(l) and len(l) < 120), None)
            if not title:
                continue
            out.append({
                "source": f"Telegram @{name}", "company": "",
                "title": title, "location": " ".join(lines)[:1500],
                "remote": None, "url": f"https://t.me/{post}", "posted": posted.isoformat(),
                "description": text,
            })
        first_id = re.search(r'data-post="[^/]+/(\d+)"', page)
        if not first_id:
            break
        url = f"https://t.me/s/{name}?before={first_id.group(1)}"
    return out


def fetch_all() -> list[dict]:
    jobs = []
    for c in CHANNELS:
        jobs.extend(channel(c))
    return jobs
