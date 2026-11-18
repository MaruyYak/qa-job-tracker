"""Решает, подходит ли вакансия: мануальный QA + удалёнка Европа/СНГ или релокация в Европу."""
import html
import re

# ---------- Роль ----------

QA_TITLE = re.compile(
    r"\b(qa|q\.a\.|quality assurance|tester|testing|test engineer|test analyst|"
    r"qa analyst|software tester|game tester|тестировщик|инженер по тестированию)\b",
    re.I,
)
AUTOMATION_TITLE = re.compile(
    r"\b(automation|automated|aqa|sdet|sdet\d?|software (development )?engineer in test|"
    r"test automation|автоматиз\w*|performance|load test\w*|penetration|pentest\w*|security)\b",
    re.I,
)
MANUAL_WORD = re.compile(r"\b(manual|мануальн\w*|ручн\w*)\b", re.I)
# Не софтверный QA (производство, фарма, стройка и т.п.)
NON_SOFTWARE = re.compile(
    r"\b(food|pharma\w*|gmp|clinical|manufactur\w*|supplier|welding|construction|"
    r"laboratory|lab |medical device|quality control inspector|qa/qc|qc inspector|"
    r"warehouse|mechanical|electrical|civil|aerospace|automotive|hvac|textile|"
    r"fsqa|forklift|fcc|aml|kyc|sox|compliance|audit\w*|contact cent(re|er)|support excellence|"
    r"monitoring|training and quality|operations (global )?quality|operations quality|inspekt\w*|inspector)\b",
    re.I,
)
NOT_A_QA_ROLE = re.compile(
    r"\b(recruiter|sales|account executive|marketing|product manager|designer|"
    r"customer support|support specialist|data analyst|developer|frontend|backend|"
    r"full[- ]?stack|devops|machine learning|ml engineer)\b",
    re.I,
)
AUTOMATION_TOOLS = re.compile(
    r"\b(selenium|playwright|cypress|webdriverio|appium|testng|junit|pytest|"
    r"rest[- ]?assured|cucumber|robot framework|k6|jmeter|gatling|puppeteer)\b",
    re.I,
)


# Не подходят по требованиям: менеджеры и аналитики
EXCLUDED_ROLE = re.compile(r"\b(manager|management|analyst|аналитик\w*|менеджер\w*)\b", re.I)
# Уровень: от Middle до Senior включительно
TOO_SENIOR = re.compile(
    r"\b(lead|leader|head|principal|staff|director|architect|chief|vp|vice president|"
    r"лид|руководител\w*|ведущий|главный)\b", re.I)
TOO_JUNIOR = re.compile(
    r"\b(junior|jr|intern|internship|trainee|graduate|entry[- ]level|apprentice|student|"
    r"джуниор|стажер\w*|стажёр\w*|младший)\b", re.I)


def title_allowed(title: str) -> bool:
    t = title or ""
    return not (EXCLUDED_ROLE.search(t) or TOO_SENIOR.search(t) or TOO_JUNIOR.search(t))


def role_match(title: str, description: str) -> tuple[bool, list[str]]:
    """Вернёт (подходит, теги)."""
    t = title or ""
    if not title_allowed(t):
        return False, []
    if not QA_TITLE.search(t):
        return False, []
    if NON_SOFTWARE.search(t):
        return False, []
    if NOT_A_QA_ROLE.search(t) and not re.search(r"\b(qa|tester|test engineer|quality assurance)\b", t, re.I):
        return False, []
    tags = []
    manual_in_title = bool(MANUAL_WORD.search(t))
    if AUTOMATION_TITLE.search(t):
        if not manual_in_title:
            return False, []  # Automation QA / SDET без упоминания manual
        tags.append("manual+auto")
    elif manual_in_title:
        tags.append("manual")
    else:
        # Общее название "QA Engineer": смотрим на описание
        d = description or ""
        manual_mentions = len(MANUAL_WORD.findall(d))
        tool_mentions = len(set(m.lower() for m in AUTOMATION_TOOLS.findall(d)))
        if manual_mentions == 0 and tool_mentions >= 3:
            return False, []  # по описанию это автоматизация
        if manual_mentions > 0:
            tags.append("manual в описании")
    return True, tags


# ---------- Локация ----------

EUROPE_COUNTRIES = [
    "albania", "andorra", "armenia", "austria", "belgium", "bosnia", "bulgaria", "croatia",
    "cyprus", "czech", "czechia", "denmark", "estonia", "finland", "france", "germany",
    "greece", "hungary", "iceland", "ireland", "italy", "latvia", "liechtenstein",
    "lithuania", "luxembourg", "malta", "moldova", "monaco", "montenegro", "netherlands",
    "north macedonia", "norway", "poland", "portugal", "romania", "serbia", "slovakia",
    "slovenia", "spain", "sweden", "switzerland", "united kingdom", "uk", "england",
    "scotland", "turkey", "türkiye", "georgia", "kazakhstan", "azerbaijan", "uzbekistan",
    "berlin", "munich", "hamburg", "amsterdam", "lisbon", "porto", "madrid", "barcelona",
    "warsaw", "krakow", "kraków", "wroclaw", "wrocław", "gdansk", "prague", "vienna",
    "budapest", "bucharest", "sofia", "belgrade", "limassol", "nicosia", "larnaca",
    "tallinn", "riga", "vilnius", "helsinki", "stockholm", "copenhagen", "oslo", "dublin",
    "london", "paris", "milan", "rome", "athens", "zurich", "zürich", "brussels",
    "tbilisi", "batumi", "almaty", "astana", "yerevan", "baku", "istanbul", "valletta",
    "malaga", "málaga", "valencia",
]
CIS_TARGET = re.compile(r"\b(georgia|tbilisi|batumi|kazakhstan|almaty|astana|грузия|тбилиси|казахстан|алматы|астана)\b", re.I)
# "Georgia" может быть штатом США
US_GEORGIA = re.compile(r"\b(atlanta|ga\b|georgia,? (usa|us|united states))", re.I)
EUROPE_REGION = re.compile(
    r"\b(europe|european|emea|eu\b|eea|cet|cest|eet|gmt|utc ?[+]? ?[0-3]\b|"
    r"utc[+-]?0?[0-4]|dach|nordics|baltics|cee|cis|снг|европ\w*)\b",
    re.I,
)
WORLDWIDE = re.compile(r"\b(worldwide|anywhere|global|any location|fully remote, any)\b", re.I)
REMOTE = re.compile(r"\b(remote|remotely|work from home|wfh|distributed|home[- ]based|удал[её]нн?\w*)\b", re.I)
NON_EU_ONLY = re.compile(
    r"\b(us only|usa only|united states only|u\.s\. only|must (be )?(located|based|reside) in the (us|united states)|"
    r"us citizens?|canada only|latam|latin america|apac only|india only|philippines only)\b",
    re.I,
)
US_LOCATION = re.compile(r"\b(united states|usa|u\.s\.|us|canada|india|brazil|mexico|philippines|australia|"
                         r"new york|san francisco|california|texas|remote,? us)\b", re.I)
RELOCATION = re.compile(
    r"\b(relocation (package|support|assistance|bonus|budget|is provided|provided|available|offered)|"
    r"relocat(e|ion) to|visa sponsorship|sponsor (your |a |the )?(work )?visa|we (will )?sponsor|"
    r"blue card|релокац\w*|переезд\w*)\b",
    re.I,
)
NO_RELOCATION = re.compile(
    r"\b(no relocation|relocation (is )?not (provided|available|offered|supported)|"
    r"(not|unable to|cannot|can't|do not|don't) (offer |provide )?(visa )?sponsor\w*|"
    r"without (visa )?sponsorship|no visa sponsorship)\b",
    re.I,
)


def _has_europe(text: str) -> bool:
    low = text.lower()
    if EUROPE_REGION.search(text):
        return True
    for c in EUROPE_COUNTRIES:
        if re.search(r"\b" + re.escape(c) + r"\b", low):
            if c == "georgia" and US_GEORGIA.search(text):
                continue
            return True
    return False


BROAD_REGION = re.compile(r"^\W*(europe|european union|eu|emea|eea|cee|dach|nordics|baltics)\b", re.I)


def location_match(location: str, description: str, remote_flag: bool | None, title: str = "") -> tuple[bool, list[str]]:
    loc = location or ""
    desc = description or ""
    tags = []
    # "Europe", "EMEA" вместо города обычно означает удалёнку по региону
    is_remote = bool(remote_flag) or bool(REMOTE.search(loc)) or bool(REMOTE.search(title or "")) \
        or bool(BROAD_REGION.search(loc))
    cis = bool(CIS_TARGET.search(loc)) and not US_GEORGIA.search(loc)
    europe_loc = _has_europe(loc)
    worldwide = bool(WORLDWIDE.search(loc))

    if is_remote:
        if NON_EU_ONLY.search(loc) or NON_EU_ONLY.search(desc[:3000]):
            remote_ok = False
        elif cis:
            remote_ok = True
            tags.append("remote СНГ")
        elif europe_loc:
            remote_ok = True
            tags.append("remote Европа")
        elif worldwide or not loc.strip() or loc.strip().lower() in {"remote", "remote job", "fully remote"}:
            # Удалёнка без явной страны: принимаем, если описание не ограничивает США и т.п.
            if US_LOCATION.search(loc):
                remote_ok = False
            else:
                remote_ok = True
                tags.append("remote весь мир")
        else:
            remote_ok = False
        if remote_ok:
            return True, tags

    if cis:
        tags.append("офис Грузия/Казахстан")
        return True, tags

    if RELOCATION.search(desc) and not NO_RELOCATION.search(desc) and (europe_loc or _has_europe(desc[:1500])):
        tags.append("релокация")
        return True, tags

    return False, []


TAG_RE = re.compile(r"<[^>]+>")


def clean_html(s: str) -> str:
    if not s:
        return ""
    s = html.unescape(s)
    s = TAG_RE.sub(" ", s)
    s = html.unescape(s)
    return re.sub(r"\s+", " ", s).strip()


def evaluate(job: dict) -> dict | None:
    """Возвращает job с тегами, если подходит, иначе None."""
    desc = clean_html(job.get("description", ""))
    ok, role_tags = role_match(job.get("title", ""), desc)
    if not ok:
        return None
    ok, loc_tags = location_match(job.get("location", ""), desc, job.get("remote"), job.get("title", ""))
    if not ok:
        return None
    # Отдельная отметка, если есть релокация, даже когда принято по удалёнке
    if "релокация" not in loc_tags and RELOCATION.search(desc) and not NO_RELOCATION.search(desc):
        loc_tags.append("релокация")
    out = dict(job)
    out["description"] = desc[:600]
    out["tags"] = role_tags + loc_tags
    return out
