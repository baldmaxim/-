"""
Запустите один раз — создаёт начальные JSON файлы данных.

Архитектура хранения:
  Excel  — для людей (загрузка/выгрузка)
  JSON   — для данных (внутреннее хранение, git-версионирование)
  MD     — для ИИ (база знаний, контекст)
"""
import json
import os
from datetime import datetime

os.makedirs('data', exist_ok=True)

today = datetime.now().strftime('%d.%m.%Y')

# ── Справочник цен → spravochnik.json ─────────────────────────────────────────
spravochnik = {
    "meta": {
        "section": "Кладка",
        "updated_at": today,
        "updated_by": "system"
    },
    "items": [
        {"nomenclatura": "Кирпич 120 мм",  "ed_izm": "м2", "cena": 1200, "valuta": "RUB", "data": today},
        {"nomenclatura": "Кирпич 250 мм",  "ed_izm": "м2", "cena": 1800, "valuta": "RUB", "data": today},
        {"nomenclatura": "СКЦ 80 мм",      "ed_izm": "м2", "cena":  900, "valuta": "RUB", "data": today}
    ]
}

with open('data/spravochnik.json', 'w', encoding='utf-8') as f:
    json.dump(spravochnik, f, ensure_ascii=False, indent=2)
print('OK: data/spravochnik.json создан')

# ── ВОР ЖК Холодов → vor_kholodov.json ────────────────────────────────────────
vor = {
    "meta": {
        "tender": "ЖК Холодов",
        "section": "Кладка",
        "loaded_at": today,
        "loaded_by": "system"
    },
    "items": [
        {"num": 1, "naimenovanie": "Устройство кирпичных стен 120 мм",                "ed_izm": "м2", "kolvo": 60},
        {"num": 2, "naimenovanie": "Устройство кирпичных стен 250 мм",                "ed_izm": "м2", "kolvo": 74},
        {"num": 3, "naimenovanie": "Устройство перегородок из камня СКЦ толщ. 80 мм", "ed_izm": "м2", "kolvo": 1000}
    ]
}

with open('data/vor_kholodov.json', 'w', encoding='utf-8') as f:
    json.dump(vor, f, ensure_ascii=False, indent=2)
print('OK: data/vor_kholodov.json создан')

# ── Маппинг → mapping.json (если не существует) ────────────────────────────────
if not os.path.exists('data/mapping.json'):
    with open('data/mapping.json', 'w', encoding='utf-8') as f:
        json.dump({}, f, ensure_ascii=False, indent=2)
    print('OK: data/mapping.json создан (пустой)')
else:
    print('OK: data/mapping.json уже существует, не трогаем')

print('\nGotovo! Zapuskay: python app.py')
