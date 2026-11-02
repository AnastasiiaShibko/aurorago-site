"""AURORA.GO — бэкенд на реальных данных.

Источники:
  * NOAA SWPC — планетарный Kp-индекс и трёхдневный прогноз (без ключа)
  * Open-Meteo — почасовая облачность по координатам точки (без ключа)

Засветка и открытость горизонта — свойство места, а не погоды,
поэтому хранятся константами в POINTS.

Схема API не изменилась: поля ответа те же, что были в синтетической версии,
поэтому фронтенд (app.js) работает без правок.
"""

from __future__ import annotations

import time
from contextlib import asynccontextmanager
from datetime import datetime, timedelta, timezone

import httpx
from fastapi import FastAPI, Query
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

import pages

# =====================================================================
# КОНСТАНТЫ ИСТОЧНИКОВ
# =====================================================================

KP_URL = "https://services.swpc.noaa.gov/products/noaa-planetary-k-index-forecast.json"
WEATHER_URL = "https://api.open-meteo.com/v1/forecast"

KP_TTL = 15 * 60        # Kp обновляется раз в 3 часа; 15 минут — с запасом
CLOUD_TTL = 30 * 60     # облачность берём из кэша полчаса
STALE_GRACE = 60 * 60   # сколько можно отдавать старое при сбое источника
NET_TIMEOUT = httpx.Timeout(8.0, connect=3.0)

# =====================================================================
# КЭШ
# =====================================================================

# ключ -> (fresh_until, stale_until, данные)
_cache: dict[str, tuple[float, float, object]] = {}


def _cache_get(key):
    return _cache.get(key)


def _cache_put(key, value, ttl):
    now = time.monotonic()
    _cache[key] = (now + ttl, now + ttl + STALE_GRACE, value)


class Sources:
    """Один httpx-клиент на всё приложение и два метода за данными."""

    def __init__(self):
        self._client: httpx.AsyncClient | None = None

    async def start(self):
        self._client = httpx.AsyncClient(
            timeout=NET_TIMEOUT,
            headers={"User-Agent": "AURORA.GO/1.0 (olympiad PROD)"},
            follow_redirects=True,
        )

    async def stop(self):
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # -----------------------------------------------------------------
    # Kp-индекс
    # -----------------------------------------------------------------

    async def kp_series(self):
        """Ряд (datetime, kp) по возрастанию времени.

        Возвращает (ряд, tag), где tag: 'live' | 'stale' | 'none'.
        """
        cached = _cache_get("kp")
        now = time.monotonic()
        if cached and now < cached[0]:
            return cached[2], "live"

        try:
            r = await self._client.get(KP_URL)
            r.raise_for_status()
            raw = r.json()

            # Формат: [["time_tag","kp","observed","noaa_scale"], [...], ...]
            rows = raw[1:] if raw and isinstance(raw[0], list) else raw

            series = []
            for row in rows:
                if isinstance(row, dict):
                    t, kp = row.get("time_tag"), row.get("kp")
                else:
                    t, kp = row[0], row[1]
                if kp is None or t is None:
                    continue
                try:
                    dt = datetime.fromisoformat(str(t).replace("Z", "+00:00"))
                except ValueError:
                    continue
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                series.append((dt, float(kp)))

            if not series:
                raise ValueError("пустой ряд Kp")

            series.sort(key=lambda x: x[0])
            _cache_put("kp", series, KP_TTL)
            return series, "live"

        except (httpx.HTTPError, ValueError, KeyError, IndexError, TypeError):
            if cached and now < cached[1]:
                return cached[2], "stale"
            return [], "none"

    # -----------------------------------------------------------------
    # Облачность
    # -----------------------------------------------------------------

    async def cloud_series(self, lat, lon):
        """Ряд {datetime(UTC): процент облачности}.

        Возвращает (ряд, tag), где tag: 'live' | 'stale' | 'none'.
        """
        key = "cloud:%.2f:%.2f" % (lat, lon)
        cached = _cache_get(key)
        now = time.monotonic()
        if cached and now < cached[0]:
            return cached[2], "live"

        params = {
            "latitude": lat,
            "longitude": lon,
            "hourly": "cloud_cover",
            "forecast_days": 3,
            "timezone": "UTC",
        }

        try:
            r = await self._client.get(WEATHER_URL, params=params)
            r.raise_for_status()
            hourly = r.json()["hourly"]
            times = hourly["time"]
            covers = hourly["cloud_cover"]

            series = {}
            for t, c in zip(times, covers):
                if c is None:
                    continue
                dt = datetime.fromisoformat(t)
                if dt.tzinfo is None:
                    dt = dt.replace(tzinfo=timezone.utc)
                series[dt] = float(c)

            if not series:
                raise ValueError("нет значений облачности")

            _cache_put(key, series, CLOUD_TTL)
            return series, "live"

        except (httpx.HTTPError, ValueError, KeyError, TypeError):
            if cached and now < cached[1]:
                return cached[2], "stale"
            return {}, "none"


sources = Sources()


# =====================================================================
# ВЫБОРКА ЗНАЧЕНИЙ ПО ВРЕМЕНИ
# =====================================================================

def pick_kp(series, moment):
    """Kp, действовавший в трёхчасовом окне, куда попадает moment.

    Окна Kp начинаются в 00, 03, 06, 09, 12, 15, 18, 21 UTC.
    Если записей до окна нет — берём ближайшую будущую (прогноз).
    """
    if not series:
        return None

    moment = moment.astimezone(timezone.utc)
    window_start = moment.replace(
        hour=(moment.hour // 3) * 3, minute=0, second=0, microsecond=0
    )

    before = [s for s in series if s[0] <= window_start]
    if before:
        return before[-1][1]

    after = [s for s in series if s[0] > window_start]
    return after[0][1] if after else None


def kp_reference_time(series, moment):
    """Момент, к которому относится выбранный Kp — для расчёта возраста."""
    if not series:
        return None

    moment = moment.astimezone(timezone.utc)
    window_start = moment.replace(
        hour=(moment.hour // 3) * 3, minute=0, second=0, microsecond=0
    )

    before = [s for s in series if s[0] <= window_start]
    if before:
        return before[-1][0]
    return series[0][0]


def pick_cloud(series, moment, tolerance_hours=1.5):
    """Облачность на ближайший час в пределах допуска."""
    if not series:
        return None

    moment = moment.astimezone(timezone.utc).replace(
        minute=0, second=0, microsecond=0
    )
    if moment in series:
        return series[moment]

    nearest = min(series, key=lambda k: abs((k - moment).total_seconds()))
    if abs((nearest - moment).total_seconds()) <= tolerance_hours * 3600:
        return series[nearest]
    return None


# =====================================================================
# ДАННЫЕ О ТОЧКАХ
# =====================================================================

POINTS = [
    {
        "id": "murmansk-centre",
        "name": "Центр Мурманска",
        "city": "Мурманск",
        "kind": "walk",
        "walk": "5 мин пешком",
        "lat": 68.97,
        "lon": 33.08,
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
        "lat": 68.99,
        "lon": 33.05,
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
        "lat": 69.01,
        "lon": 33.10,
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
        "lat": 68.98,
        "lon": 33.03,
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
        "lat": 69.04,
        "lon": 33.14,
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
        "lat": 68.95,
        "lon": 33.06,
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
        "lat": 67.61,
        "lon": 33.73,
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
        "lat": 67.75,
        "lon": 33.55,
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
        "lat": 68.00,
        "lon": 35.02,
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
        "lat": 69.16,
        "lon": 35.14,
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
        "lat": 67.16,
        "lon": 32.41,
        "light_pollution": 12,
        "horizon": 0.86,
        "about": "Юг области, больше ясных ночей, чем в Мурманске.",
    },
]

POINT_BY_ID = {p["id"]: p for p in POINTS}


# =====================================================================
# ИНТЕРВАЛЫ
# =====================================================================

_WD = ["пн", "вт", "ср", "чт", "пт", "сб", "вс"]


def _weekday(dt):
    return _WD[dt.weekday()] + " " + dt.strftime("%d.%m")


def _build_intervals():
    """Восемь трёхчасовых окон: две ночи подряд, начиная с ближайших 18:00.

    Если сейчас до полуночи — первая ночь сегодняшняя.
    Если уже ночь/утро — первая ночь начнётся сегодня вечером.
    """
    now = datetime.now().astimezone()
    start = now.replace(hour=18, minute=0, second=0, microsecond=0)
    if now >= start:
        start += timedelta(days=1)

    out = []
    for i in range(8):
        night = i // 4
        block = i % 4
        begin = start + timedelta(days=night, hours=block * 3)
        end = begin + timedelta(hours=3)
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


INTERVALS = _build_intervals()
INTERVAL_BY_ID = {i["id"]: i for i in INTERVALS}


def _refresh_intervals():
    """Окна пересобираются по запросу, чтобы не протухали за ночь."""
    global INTERVALS, INTERVAL_BY_ID
    fresh = _build_intervals()
    INTERVALS = fresh
    INTERVAL_BY_ID = {i["id"]: i for i in fresh}
    return fresh


# =====================================================================
# МОДЕЛЬ ОЦЕНКИ
# =====================================================================

ACC_BONUS = {"walk": 0.50, "taxi": 0.80, "transfer": 1.00}
WEIGHTS = {"kp": 0.45, "cloud": 0.30, "lp": 0.15, "acc": 0.10}


def _clamp(v, lo=0.0, hi=1.0):
    return max(lo, min(hi, v))


def _score(point, kp, cloud):
    if kp is None or cloud is None:
        return None, None

    f_kp = _clamp(kp / 9.0)                  # реальная шкала Kp: 0..9
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
            "Для этого интервала не хватает данных: Kp-индекс или облачность "
            "не получены от источника. Мы не подставляем средние значения — "
            "лучше честное «нет данных», чем ложная уверенность."
        )

    items = [
        ("магнитная активность", parts["kp"]),
        ("облачность", parts["cloud"]),
        ("засветка точки", parts["lp"]),
        ("доступность", parts["acc"]),
    ]
    items.sort(key=lambda x: x[1])
    weak_name, _ = items[0]
    strong_name, strong_v = items[-1]

    lead = {
        "магнитная активность": "Главное ограничение — слабая магнитная активность",
        "облачность": "Главное ограничение — облачность",
        "засветка точки": "Главное ограничение — городская засветка",
        "доступность": "Главное ограничение — дорога до точки",
    }[weak_name]

    text = "%s (Kp %s, облачность %s%%). " % (lead, kp, cloud)
    if strong_v >= 0.8:
        text += "Зато %s в вашу пользу. " % strong_name

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
            "note": "Kp-индекс не получен от NOAA",
        })
    else:
        rows.append({
            "key": "kp", "label": "Магнитная активность",
            "value": str(round(kp, 1)), "unit": "", "part": _clamp(kp / 9.0),
            "note": "Планетарный Kp-индекс, шкала 0–9",
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
            "note": "Доля закрытого неба по Open-Meteo",
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


# =====================================================================
# СБОРКА ПРОГНОЗА
# =====================================================================

async def _observation(point, interval):
    """Возвращает (kp, cloud, age_minutes, tag).

    tag: 'live' — оба источника свежие
         'stale' — хотя бы один отдал данные из кэша при сбое
         'none'  — данных нет совсем
    """
    begin = datetime.fromisoformat(interval["iso"]).astimezone(timezone.utc)

    kp_series, kp_tag = await sources.kp_series()
    kp = pick_kp(kp_series, begin)

    cloud_series, cloud_tag = await sources.cloud_series(point["lat"], point["lon"])
    cloud_raw = pick_cloud(cloud_series, begin)
    cloud = int(round(cloud_raw)) if cloud_raw is not None else None

    tags = (kp_tag, cloud_tag)
    if "none" in tags:
        tag = "none"
    elif "stale" in tags:
        tag = "stale"
    else:
        tag = "live"

        age = None
    ref = kp_reference_time(kp_series, begin)
    if ref is not None:
        age = int((datetime.now(timezone.utc) - ref).total_seconds() // 60)
        # Kp прошедшего окна всегда «старше» своего начала — это нормально.
        # Показываем возраст только если данные реально устарели.
        if age < 0 or age < 240:
            age = 0

    return kp, cloud, age, tag


async def build_forecast(point_id, interval_id):
    point = POINT_BY_ID.get(point_id)
    interval = INTERVAL_BY_ID.get(interval_id)
    if not point or not interval:
        return None

    kp, cloud, age, tag = await _observation(point, interval)
    score, parts = _score(point, kp, cloud)
    verdict, note = _verdict(score)

    if kp is None or cloud is None:
        status = "missing"
    elif tag == "stale" or (age is not None and age >= 180):
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
        "age_minutes": age if age is not None else 0,
        "factors": _factor_rows(point, kp, cloud, age),
        "explanation": _explanation(point, score, parts, kp, cloud),
        "source": "NOAA SWPC + Open-Meteo",
    }


# =====================================================================
# ПРИЛОЖЕНИЕ
# =====================================================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    await sources.start()
    yield
    await sources.stop()


app = FastAPI(title="AURORA.GO", lifespan=lifespan)


# =====================================================================
# API
# =====================================================================

@app.get("/api/points")
def api_points():
    return POINTS

@app.get("/api/intervals")
def api_intervals():
    return _refresh_intervals()


@app.get("/api/status")
async def api_status():
    """Диагностика: отвечают ли внешние источники. Удобно для отладки."""
    kp_series, kp_tag = await sources.kp_series()
    cloud_probe, cloud_tag = await sources.cloud_series(68.97, 33.08)
    return {
        "kp": {
            "tag": kp_tag,
            "records": len(kp_series),
            "latest": kp_series[-1][1] if kp_series else None,
            "latest_time": kp_series[-1][0].isoformat() if kp_series else None,
        },
        "cloud_probe_murmansk": {
            "tag": cloud_tag,
            "records": len(cloud_probe),
        },
        "cache_keys": len(_cache),
    }


@app.get("/api/forecast")
async def api_forecast(
    point_id: str = Query(...),
    interval_id: str = Query(...),
):
    data = await build_forecast(point_id, interval_id)
    if data is None:
        return {"error": "unknown point_id or interval_id"}
    return data


@app.get("/api/overview")
async def api_overview(interval_id: str = Query(...)):
    _refresh_intervals()
    if interval_id not in INTERVAL_BY_ID:
        return {"error": "unknown interval_id", "results": []}
    ...

    out = []
    seen_kp = None
    for p in POINTS:
        f = await build_forecast(p["id"], interval_id)
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
        if seen_kp is None:
            for row in f["factors"]:
                if row["key"] == "kp":
                    seen_kp = row["value"]
                    break

    return {
        "interval_id": interval_id,
        "kp": seen_kp,
        "results": out,
    }


class CompareRequest(BaseModel):
    mode: str = "points"
    point_ids: list[str] = []
    interval_ids: list[str] = []


@app.post("/api/compare")
async def api_compare(req: CompareRequest):
    results = []

    if req.mode == "points":
        interval_id = req.interval_ids[0] if req.interval_ids else None
        if interval_id not in INTERVAL_BY_ID:
            return {"error": "unknown interval_id", "results": []}
        for pid in req.point_ids:
            f = await build_forecast(pid, interval_id)
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
            f = await build_forecast(point_id, iid)
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

    if req.mode == "points":
        best_id = best["point_id"] if best else None
    else:
        best_id = best["interval_id"] if best else None

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
@app.get("/api/kinds")
def api_kinds():
    return {
        "ru": {"walk": "Пешком", "taxi": "Такси", "transfer": "Трансфер"},
        "short": {"walk": "пешком", "taxi": "такси", "transfer": "трансфер"},
    }