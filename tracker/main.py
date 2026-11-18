"""Запуск: python -m tracker.main

Собирает вакансии из всех источников, фильтрует и обновляет data/jobs.json и docs/jobs.json.
"""
import concurrent.futures as cf
import datetime as dt
import hashlib
import json
import logging
import os
import pathlib
import re

from .filters import evaluate
from .sources import ats, boards, telegram

ROOT = pathlib.Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "jobs.json"
SITE_DATA = ROOT / "docs" / "jobs.json"
COMPANIES = ROOT / "companies.json"
KEEP_DAYS = 60  # вакансии, которых нет в источниках дольше, удаляются

logging.basicConfig(level=logging.INFO, format="%(levelname)s %(message)s")
log = logging.getLogger("tracker")


def collect() -> tuple[list[dict], dict]:
    tasks = []
    companies = json.loads(COMPANIES.read_text())
    for ats_name, slugs in companies.items():
        fn = ats.FETCHERS[ats_name]
        for slug in slugs:
            tasks.append((f"{ats_name}:{slug}", fn, (slug,)))
    for name, fn in boards.FETCHERS.items():
        tasks.append((name, fn, ()))
    tasks.append(("telegram", telegram.fetch_all, ()))

    jobs, stats = [], {}
    workers = int(os.environ.get("TRACKER_WORKERS", "12"))
    # Workable сильно ограничивает частоту, поэтому запускаем его последовательно
    serial = [t for t in tasks if t[0].startswith("workable:")]
    parallel = [t for t in tasks if not t[0].startswith("workable:")]

    def run(t):
        name, fn, args = t
        try:
            return name, fn(*args)
        except Exception as e:  # один сломанный источник не должен ронять весь сбор
            log.warning("%s failed: %s", name, e)
            return name, []

    with cf.ThreadPoolExecutor(workers) as ex:
        for name, res in ex.map(run, parallel):
            stats[name] = len(res)
            jobs.extend(res)
    for t in serial:
        name, res = run(t)
        stats[name] = len(res)
        jobs.extend(res)
    return jobs, stats


def job_id(j: dict) -> str:
    key = j.get("url") or f"{j.get('company')}|{j.get('title')}"
    return hashlib.sha1(key.encode()).hexdigest()[:12]


def dedupe_key(j: dict) -> str:
    norm = lambda s: re.sub(r"[^a-z0-9]", "", (s or "").lower())
    return norm(j.get("company")) + "|" + norm(j.get("title"))


def main():
    now = dt.datetime.now(dt.timezone.utc).replace(microsecond=0).isoformat()
    raw, stats = collect()
    log.info("Собрано всего: %d", len(raw))

    matched = {}
    seen_keys = set()
    for j in raw:
        if not j.get("url"):
            continue
        ev = evaluate(j)
        if not ev:
            continue
        k = dedupe_key(ev)
        if k in seen_keys:
            continue
        seen_keys.add(k)
        ev["id"] = job_id(ev)
        matched[ev["id"]] = ev
    log.info("Подходит: %d", len(matched))

    old = {}
    if DATA.exists():
        old = {j["id"]: j for j in json.loads(DATA.read_text()).get("jobs", [])}

    result = []
    for jid, j in matched.items():
        prev = old.get(jid, {})
        j["first_seen"] = prev.get("first_seen", now)
        j["last_seen"] = now
        j["active"] = True
        result.append(j)
    cutoff = dt.datetime.now(dt.timezone.utc) - dt.timedelta(days=KEEP_DAYS)
    for jid, j in old.items():
        if jid in matched:
            continue
        if dt.datetime.fromisoformat(j["last_seen"]) >= cutoff:
            j["active"] = False  # пропала из источника: скорее всего закрыта
            result.append(j)

    result.sort(key=lambda j: (j["first_seen"], j.get("posted") or ""), reverse=True)
    payload = {"updated": now, "count": len(result), "sources": stats, "jobs": result}
    for p in (DATA, SITE_DATA):
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps(payload, ensure_ascii=False, indent=1))
    new = sum(1 for j in result if j["first_seen"] == now)
    log.info("Новых сегодня: %d", new)
    _notify_telegram([j for j in result if j["first_seen"] == now])


def _notify_telegram(new_jobs: list[dict]):
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not (token and chat and new_jobs):
        return
    from .http import session
    for chunk in range(0, len(new_jobs), 10):
        lines = [f"<b>Новые вакансии QA</b> ({len(new_jobs)})"] if chunk == 0 else []
        for j in new_jobs[chunk:chunk + 10]:
            tags = ", ".join(j.get("tags", []))
            lines.append(f'• <a href="{j["url"]}">{_esc(j["title"])}</a> · {_esc(j["company"])}\n  {_esc(j.get("location", ""))} [{tags}]')
        session.post(f"https://api.telegram.org/bot{token}/sendMessage",
                     data={"chat_id": chat, "text": "\n".join(lines), "parse_mode": "HTML",
                           "disable_web_page_preview": "true"}, timeout=30)


def _esc(s):
    return (s or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


if __name__ == "__main__":
    main()
