import logging
import time

import requests

log = logging.getLogger("tracker")

session = requests.Session()
_adapter = requests.adapters.HTTPAdapter(pool_connections=20, pool_maxsize=20)
session.mount("https://", _adapter)
session.headers.update({"User-Agent": "Mozilla/5.0 (personal QA job tracker)"})


def get(url, params=None, retries=2, **kw):
    for attempt in range(retries + 1):
        try:
            r = session.get(url, params=params, timeout=30, **kw)
            if r.status_code == 429 and attempt < retries:
                time.sleep(min(int(r.headers.get("Retry-After", 0) or 0), 60) or 10 * (attempt + 1))
                continue
            if r.status_code == 404:
                return None
            r.raise_for_status()
            return r
        except requests.RequestException as e:
            if attempt == retries:
                log.warning("GET %s failed: %s", url, e)
                return None
            time.sleep(2)
    return None


def get_json(url, params=None, **kw):
    r = get(url, params=params, **kw)
    if r is None:
        return None
    try:
        return r.json()
    except ValueError:
        log.warning("Not JSON: %s", url)
        return None
