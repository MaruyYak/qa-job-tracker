# Manual QA job tracker

Личный трекер вакансий **Manual QA Engineer**: удалёнка по Европе/СНГ (Грузия, Казахстан) или релокация в Европу.

Каждый день в 05:00 UTC GitHub Actions собирает вакансии, отфильтровывает подходящие и обновляет страницу `docs/index.html`.

## Источники
- Карьерные страницы компаний через открытые API: Greenhouse, Lever, Ashby, SmartRecruiters (список в `companies.json`).
- Доски вакансий: Arbeitnow, Remotive, RemoteOK, Himalayas, Jobicy, We Work Remotely.
- Telegram-каналы: список в `tracker/sources/telegram.py`.
- LinkedIn, hh.kz, Djinni, Relocate.me: готовые ссылки-поиски внизу страницы (автоматический сбор там запрещён или закрыт).

## Фильтры (`tracker/filters.py`)
- Уровень: от Middle до Senior. Отбрасываются Junior/Intern/Trainee, Lead/Head/Principal/Staff/Director, а также любые Manager и Analyst.
- Роль: QA / Tester / Quality Assurance в названии. Отбрасываются Automation, AQA, SDET, Performance, Security, если в названии нет слова Manual. Если название общее («QA Engineer»), а в описании нет слова manual и упомянуто 3+ инструмента автоматизации, вакансия тоже отбрасывается.
- Локация: remote в Европе/EMEA/СНГ, remote без ограничения страны, офис в Грузии/Казахстане, или явная релокация/визовая поддержка в Европу.

## Как добавить компанию
Добавьте slug в нужный раздел `companies.json`. Slug берётся из адреса карьерной страницы:
`boards.greenhouse.io/<slug>`, `jobs.lever.co/<slug>`, `jobs.ashbyhq.com/<slug>`, `jobs.smartrecruiters.com/<slug>`.

## Уведомления в Telegram (по желанию)
Добавьте в Settings → Secrets and variables → Actions секреты `TELEGRAM_BOT_TOKEN` и `TELEGRAM_CHAT_ID`.

## Запуск вручную
```
pip install -r requirements.txt
python -m tracker.main
```
