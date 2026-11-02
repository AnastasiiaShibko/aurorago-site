"""AURORA.GO — бэкенд.

Синтетический датасет: все значения детерминированно выводятся из
хэша (точка, интервал), поэтому страница не меняется при перезагрузке.
"""

from __future__ import annotations

import hashlib
from datetime import datetime, timedelta

from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import pages

app = FastAPI(title="AURORA.GO")


# =====================================================================
# ДАННЫЕ
# =====================================================================

POINTS = [
    {
        "id": "murmansk-centre",
        "name": "Центр Мурманска",
        "city": "Мурманск",
        "kind": "walk",
        "walk": "5 мин пешком",
        "light_pollution": 35,
        "horizon": 0.45,
        "about": "Пятиэтажки закрывают север. Годится только при сильной буре.",
    },
    {
        "id": "murmansk-memorial",
        "name": "Мемориал Защитникам",
        "city": "Мурманск",
        "kind": "walk",
        "walk": "15 мин пешком",
        "light_pollution": 30,
        "horizon": 0.62,
        "about": "Высокая точка над городом, но фонари мешают с юга.",
    },
    {
        "id": "semcon",
        "name": "Семёновские сопки",
        "city": "Мурманск",
        "kind": "walk",
        "walk": "25 мин пешком",
        "light_pollution": 18,
        "horizon": 0.88,
        "about": "Открытый север без единого фонаря. Лучшая пешая точка города.",
    },
    {
        "id": "abram-mys",
        "name": "Абрам-Мыс",
        "city": "Мурманск",
        "kind": "walk",
        "walk": "30 мин пешком",
        "light_pollution": 26,
        "horizon": 0.74,
        "about": "Вид через залив на город — красиво, но засветка с юга.",
    },
    {
        "id": "zelenets",
        "name": "Зелёный мыс",
        "city": "Мурманск",
        "kind": "walk",
        "walk": "20 мин пешком",
        "light_pollution": 22,
        "horizon": 0.82,
        "about": "Тихий берег, север открыт полностью. Много снега зимой.",
    },
    {
        "id": "murmansk-bridge",
        "name": "Мост через залив",
        "city": "Мурманск",
        "kind": "walk",
        "walk": "35 мин пешком",
        "light_pollution": 28,
        "horizon": 0.70,
        "about": "Панорама залива. Ветер сильнее, чем кажется с берега.",
    },
    {
        "id": "kirovsk",
        "name": "Кировск, Хибины",
        "city": "Кировск",
        "kind": "transfer",
        "walk": "3 ч на машине",
        "light_pollution": 8,
        "horizon": 0.90,
        "about": "Город в горах. Тёмное небо, но нужна ночёвка.",
    },
    {
        "id": "kirovsk-pass",
        "name": "Перевал Рамзая",
        "city": "Кировск",
        "kind": "transfer",
        "walk": "3.5 ч на машине",
        "light_pollution": 4,
        "horizon": 0.96,
        "about": "Самое тёмное место области. Зимой перевал закрывают.",
    },
    {
        "id": "lovozero",
        "name": "Ловозеро",
        "city": "Ловозеро",
        "kind": "transfer",
        "walk": "4 ч на машине",
        "light_pollution": 6,
        "horizon": 0.92,
        "about": "Тундра и горы Ловозёрских тундр. Связи нет.",
    },
    {
        "id": "teriberka",
        "name": "Териберка",
        "city": "Териберка",
        "kind": "taxi",
        "walk": "2 ч на такси",
        "light_pollution": 10,
        "horizon": 0.94,
        "about": "Берег Баренцева моря, открытый горизонт со всех сторон.",
    },
    {
        "id": "kandalaksha",
        "name": "Кандалакша",
        "city": "Кандалакша",
        "kind": "taxi",
        "walk": "2.5 ч на такси",
        "light_pollution": 12,
        "horizon": 0.86,
        "about": "Юг области, больше ясных ночей, чем в Мурманске.",
    },
]

POINT_BY_ID = {p["id"]: p for p in POINTS}


def _build_intervals():
    """Восемь трёхчасовых окон: две ночи подряд."""
    now = datetime.now()
    start = now.replace(hour=18, minute=0, second=0, microsecond=0)
    raw = []
    for night in range(2):
        base = start + timedelta(days=night)
        for block in range(4):
            begin = base + timedelta(hours=block * 3)
            end = begin + timedelta(hours=3)
            raw.append((night, begin, end))

    out = []
    for i, (night, begin, end) in enumerate(raw):
        out.append({
            "id": "iv-%02d" % (i + 1),
            "label": "%02d–%02d" % (begin.hour, end.hour % 24),
            "title": "%s, %s–%s" % (
                _weekday(begin),
                begin.strftime("%H:%M"),
                end.strftime("%H:%M"),
            ),
            "night": night + 1,
            "iso": begin.isoformat(timespec="minutes"),
        })
    return out


_WD = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def _weekday(dt):
    return _WD[dt.weekday()] + " " + dt.strftime("%d.%m")


INTERVALS = _build_intervals()
INTERVAL_BY_ID = {i["id"]: i for i in INTERVALS}


# =====================================================================
# ДЕТЕРМИНИРОВАННЫЙ ГЕНЕРАТОР
# =====================================================================

def _h(*parts):
    """Стабильное число 0..1 из набора ключей."""
    key = "|".join(str(p) for p in parts)
    digest = hashlib.sha256(key.encode("utf-8")).hexdigest()[:8]
    return int(digest, 16) / 0xFFFFFFFF


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


ACC_BONUS = {"walk": 0.50, "taxi": 0.80, "transfer": 1.00}

WEIGHTS = {"kp": 0.45, "cloud": 0.30, "lp": 0.15, "acc": 0.10}


def _observation(point, interval):
    """Сырые значения: (kp, cloud, age_minutes)."""
    kp = round(1.5 + _h("kp", interval["id"]) * 7.0, 1)
    cloud = int(round(_h("cloud", point["id"], interval["id"]) * 100))
    age = int(round(_h("age", point["id"]) * 280))

    if _h("miss-kp", point["id"], interval["id"]) < 0.06:
        kp = None
    if _h("miss-cloud", point["id"], interval["id"]) < 0.06:
        cloud = None

    return kp, cloud, age


def _score(point, kp, cloud):
    if kp is None or cloud is None:
        return None, None

    f_kp = _clamp((kp - 1.5) / 7.0)
    f_cloud = _clamp(1.0 - cloud / 100.0)
    f_lp = _clamp(1.0 - point["light_pollution"] / 100.0)
    f_acc = _clamp(0.5 * point["horizon"] + 0.5 * ACC_BONUS[point["kind"]])

    score = 100.0 * (
        WEIGHTS["kp"] * f_kp
        + WEIGHTS["cloud"] * f_cloud
        + WEIGHTS["lp"] * f_lp
        + WEIGHTS["acc"] * f_acc
    )
    parts = {"kp": f_kp, "cloud": f_cloud, "lp": f_lp, "acc": f_acc}
    return round(score, 1), parts


def _verdict(score):
    if score is None:
        return "Нет данных", "Не хватает наблюдений — оценка не рассчитана."
    if score < 20:
        return "Бесполезно", "Небо закрыто или магнитуда слишком низкая. Вечер не стоит тратить."
    if score < 40:
        return "Слабая", "Шанс есть только в очень тёмном месте и с терпением."
    if score < 60:
        return "Небольшая", "Реальный шанс, если уехать от огней и смотреть на север."
    if score < 80:
        return "Хорошая", "Стоит выехать. Условия складываются в вашу пользу."
    return "Отличная", "Выезжайте заранее и занимайте точку до пика."


def _explanation(point, score, parts, kp, cloud):
    if score is None:
        return (
            "Для этой комбинации нет полных наблюдений. Мы не подставляем "
            "средние значения: лучше честное «нет данных», чем ложная уверенность."
        )

    items = [
        ("kp", "магнитная активность", parts["kp"]),
        ("cloud", "облачность", parts["cloud"]),
        ("lp", "засветка точки", parts["lp"]),
        ("acc", "доступность", parts["acc"]),
    ]
    items.sort(key=lambda x: x[2])
    weak, _, _ = items[0]
    _, strong, strong_v = items[-1]

    lead = {
        "kp": "Главное ограничение — слабая магнитная активность",
        "cloud": "Главное ограничение — облачность",
        "lp": "Главное ограничение — городская засветка",
        "acc": "Главное ограничение — дорога до точки",
    }[weak]

    text = "%s (Kp %s, облачность %s%%). " % (lead, kp, cloud)
    if strong_v >= 0.8:
        text += "Зато %s в вашу пользу. " % strong
    if point["kind"] == "transfer":
        text += "Это выездная точка: планируйте ночёвку и обратную дорогу."
    elif point["kind"] == "walk":
        text += "Дойти можно пешком, возвращаться ночью — с фонарём."
    else:
        text += "Такси туда и обратно лучше заказать заранее."
    return text


def _factor_rows(point, kp, cloud, age):
    rows = []

    if kp is None:
        rows.append({
            "key": "kp", "label": "Магнитная активность",
            "value": "—", "unit": "", "part": None,
            "note": "Наблюдение Kp-индекса отсутствует",
        })
    else:
        rows.append({
            "key": "kp", "label": "Магнитная активность",
            "value": str(kp), "unit": "", "part": _clamp((kp - 1.5) / 7.0),
            "note": "Kp-индекс: от 1.5 до 8.5",
        })

    if cloud is None:
        rows.append({
            "key": "cloud", "label": "Облачность",
            "value": "—", "unit": "%", "part": None,
            "note": "Метеоданные не получены",
        })
    else:
        rows.append({
            "key": "cloud", "label": "Облачность",
            "value": str(cloud), "unit": "%", "part": _clamp(1.0 - cloud / 100.0),
            "note": "Доля закрытого неба",
        })

    rows.append({
        "key": "lp", "label": "Засветка точки",
        "value": str(point["light_pollution"]), "unit": "%",
        "part": _clamp(1.0 - point["light_pollution"] / 100.0),
        "note": "Городской свет в направлении севера",
    })
    rows.append({
        "key": "acc", "label": "Горизонт и доступ",
        "value": str(int(round(point["horizon"] * 100))), "unit": "%",
        "part": _clamp(0.5 * point["horizon"] + 0.5 * ACC_BONUS[point["kind"]]),
        "note": "Открытость северного горизонта и способ добраться",
    })
    return rows


def build_forecast(point_id, interval_id):
    point = POINT_BY_ID.get(point_id)
    interval = INTERVAL_BY_ID.get(interval_id)
    if not point or not interval:
        return None

    kp, cloud, age = _observation(point, interval)
    score, parts = _score(point, kp, cloud)
    verdict, note = _verdict(score)

    if kp is None or cloud is None:
        status = "missing"
    elif age >= 180:
        status = "stale"
    else:
        status = "fresh"

    return {
        "point_id": point["id"],
        "point_name": point["name"],
        "interval_id": interval["id"],
        "interval_label": interval["title"],
        "score": score,
        "verdict": verdict,
        "verdict_note": note,
        "data_status": status,
        "age_minutes": age,
        "factors": _factor_rows(point, kp, cloud, age),
        "explanation": _explanation(point, score, parts, kp, cloud),
        "source": "синтетический датасет",
    }


# =====================================================================
# API
# =====================================================================

@app.get("/api/points")
def api_points():
    return POINTS


@app.get("/api/intervals")
def api_intervals():
    return INTERVALS


@app.get("/api/forecast")
def api_forecast(
    point_id: str = Query(...),
    interval_id: str = Query(...),
):
    data = build_forecast(point_id, interval_id)
    if data is None:
        return {"error": "unknown point_id or interval_id"}
    return data


@app.get("/api/overview")
def api_overview(interval_id: str = Query(...)):
    if interval_id not in INTERVAL_BY_ID:
        return {"error": "unknown interval_id", "results": []}
    out = []
    for p in POINTS:
        f = build_forecast(p["id"], interval_id)
        out.append({
            "point_id": p["id"],
            "point_name": p["name"],
            "city": p["city"],
            "kind": p["kind"],
            "walk": p["walk"],
            "about": p["about"],
            "score": f["score"],
            "verdict": f["verdict"],
            "data_status": f["data_status"],
        })
    return {"interval_id": interval_id, "results": out}


class CompareRequest(BaseModel):
    mode: str = "points"
    point_ids: list[str] = []
    interval_ids: list[str] = []


@app.post("/api/compare")
def api_compare(req: CompareRequest):
    results = []

    if req.mode == "points":
        interval_id = req.interval_ids[0] if req.interval_ids else None
        if interval_id not in INTERVAL_BY_ID:
            return {"error": "unknown interval_id", "results": []}
        for pid in req.point_ids:
            f = build_forecast(pid, interval_id)
            if not f:
                continue
            results.append({
                "point_id": pid,
                "point_name": f["point_name"],
                "interval_id": interval_id,
                "interval_label": f["interval_label"],
                "score": f["score"],
                "verdict": f["verdict"],
            })
    else:
        point_id = req.point_ids[0] if req.point_ids else None
        if point_id not in POINT_BY_ID:
            return {"error": "unknown point_id", "results": []}
        for iid in req.interval_ids:
            f = build_forecast(point_id, iid)
            if not f:
                continue
            results.append({
                "point_id": point_id,
                "point_name": f["point_name"],
                "interval_id": iid,
                "interval_label": f["interval_label"],
                "score": f["score"],
                "verdict": f["verdict"],
            })

    scored = [r for r in results if r["score"] is not None]
    best = max(scored, key=lambda r: r["score"]) if scored else None
    best_id = best["point_id"] if req.mode == "points" and best else (
        best["interval_id"] if best else None
    )

    if best is None:
        explanation = "Ни по одной позиции нет полных данных — сравнить нечего."
    elif req.mode == "points":
        explanation = "Лучший вариант: <b>%s</b> — %.1f из 100, «%s»." % (
            best["point_name"], best["score"], best["verdict"].lower()
        )
    else:
        explanation = "Лучшее окно: <b>%s</b> — %.1f из 100, «%s»." % (
            best["interval_label"], best["score"], best["verdict"].lower()
        )

    return {
        "mode": req.mode,
        "results": results,
        "best_id": best_id,
        "explanation": explanation,
        "disclaimer": (
            "Разница меньше 5 баллов находится в пределах погрешности модели."
        ),
    }


# =====================================================================
# СТРАНИЦЫ
# =====================================================================

@app.get("/", response_class=HTMLResponse)
def page_main():
    return pages.PAGE


@app.get("/spots", response_class=HTMLResponse)
def page_spots():
    return pages.SPOTS


@app.get("/method", response_class=HTMLResponse)
def page_method():
    return pages.METHOD


@app.get("/faq", response_class=HTMLResponse)
def page_faq():
    return pages.FAQ


@app.get("/about", response_class=HTMLResponse)
def page_about():
    return pages.ABOUT


@app.get("/guide/watch", response_class=HTMLResponse)
def page_watch():
    return pages.WATCH


@app.get("/guide/photo", response_class=HTMLResponse)
def page_photo():
    return pages.PHOTO


@app.get("/guide/pack", response_class=HTMLResponse)
def page_pack():
    return pages.PACK


app.mount("/static", StaticFiles(directory="static"), name="static")
import httpx