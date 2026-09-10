from math import ceil
from pathlib import Path

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from starlette.requests import Request

from .cities import ALL_CITIES
from .weather import WeatherError, get_all, get_current

app = FastAPI(title="Weather Service", description="Удобная работа с OpenWeather API")

BASE_DIR = Path(__file__).resolve().parent
templates = Jinja2Templates(directory=str(BASE_DIR / "templates"))


def paginate(items: list, page: int, size: int) -> dict:
    total = len(items)
    pages = max(1, ceil(total / size))
    page = min(max(1, page), pages)
    start = (page - 1) * size
    return {
        "items": items[start:start + size],
        "page": page,
        "size": size,
        "total": total,
        "pages": pages,
    }


async def ranked(sort_key, reverse: bool, page: int, size: int) -> dict:
    data = await get_all(ALL_CITIES)
    if not data:
        raise HTTPException(status_code=404, detail="Не удалось получить данные ни по одному городу")
    data = sorted(data, key=sort_key, reverse=reverse)
    return paginate(data, page, size)


@app.get("/", response_class=HTMLResponse)
async def index(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


@app.get("/api/health")
async def health():
    return {"status": "ok"}


@app.get("/api/weather")
async def api_weather(city: str = Query(..., description="Название города")):
    try:
        return await get_current(city)
    except WeatherError as e:
        raise HTTPException(status_code=404, detail=str(e))


@app.get("/api/coldest")
async def api_coldest(page: int = Query(1, ge=1), size: int = Query(12, ge=1, le=100)):
    return await ranked(lambda x: x["temp"], False, page, size)


@app.get("/api/hottest")
async def api_hottest(page: int = Query(1, ge=1), size: int = Query(12, ge=1, le=100)):
    return await ranked(lambda x: x["temp"], True, page, size)


@app.get("/api/humidity")
async def api_humidity(page: int = Query(1, ge=1), size: int = Query(12, ge=1, le=100)):
    return await ranked(lambda x: (x["humidity"] or 0), True, page, size)
