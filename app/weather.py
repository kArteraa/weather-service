import asyncio
import time

import httpx

from .config import CACHE_TTL, LANG, MAX_CONCURRENCY, OWM_API_KEY, OWM_BASE_URL, UNITS


class WeatherError(Exception):
    pass


_cache: dict[str, tuple[float, list[dict]]] = {}


def _parse(data: dict) -> dict:
    weather = (data.get("weather") or [{}])[0]
    main = data.get("main", {})
    wind = data.get("wind", {})
    sys = data.get("sys", {})

    return {
        "city": data.get("name"),
        "country": sys.get("country"),
        "description": weather.get("description", "").capitalize(),
        "icon": weather.get("icon"),
        "temp": round(main.get("temp", 0)),
        "feels_like": round(main.get("feels_like", 0)),
        "temp_min": round(main.get("temp_min", 0)),
        "temp_max": round(main.get("temp_max", 0)),
        "humidity": main.get("humidity"),
        "pressure": main.get("pressure"),
        "wind_speed": wind.get("speed"),
        "clouds": data.get("clouds", {}).get("all"),
    }


async def _fetch(client: httpx.AsyncClient, city: str) -> dict:
    params = {
        "q": city,
        "appid": OWM_API_KEY,
        "units": UNITS,
        "lang": LANG,
    }
    resp = await client.get(OWM_BASE_URL, params=params, timeout=10.0)
    if resp.status_code == 404:
        raise WeatherError(f"Город «{city}» не найден")
    if resp.status_code == 401:
        raise WeatherError("Неверный API-ключ OpenWeather")
    resp.raise_for_status()
    return _parse(resp.json())


async def get_current(city: str) -> dict:
    async with httpx.AsyncClient() as client:
        return await _fetch(client, city)


async def get_many(cities: list[str]) -> list[dict]:
    semaphore = asyncio.Semaphore(MAX_CONCURRENCY)

    async with httpx.AsyncClient() as client:
        async def guarded(city: str) -> dict:
            async with semaphore:
                return await _fetch(client, city)

        results = await asyncio.gather(*[guarded(c) for c in cities], return_exceptions=True)

    return [r for r in results if not isinstance(r, Exception)]


async def get_all(cities: list[str]) -> list[dict]:
    key = ",".join(cities)
    now = time.time()
    cached = _cache.get(key)
    if cached and now - cached[0] < CACHE_TTL:
        return cached[1]

    data = await get_many(cities)
    _cache[key] = (now, data)
    return data
