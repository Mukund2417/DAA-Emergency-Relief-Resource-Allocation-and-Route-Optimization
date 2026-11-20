"""India-focused live context from public weather services."""
from datetime import datetime, timezone

import httpx
from fastapi import APIRouter, HTTPException, Query

router = APIRouter(prefix="/india", tags=["India live data"])
TIMEOUT = httpx.Timeout(10.0, connect=5.0)


async def fetch_json(url: str, params: dict):
    try:
        async with httpx.AsyncClient(timeout=TIMEOUT, follow_redirects=True) as client:
            response = await client.get(url, params=params)
            response.raise_for_status()
            return response.json()
    except (httpx.HTTPError, ValueError) as exc:
        raise HTTPException(502, "The live weather service is temporarily unavailable. Please try again.") from exc


@router.get("/places")
async def search_indian_places(name: str = Query(min_length=2, max_length=100)):
    payload = await fetch_json(
        "https://geocoding-api.open-meteo.com/v1/search",
        {"name": name.strip(), "count": 10, "language": "en", "format": "json"},
    )
    results = [
        {
            "name": item.get("name"),
            "admin1": item.get("admin1"),
            "admin2": item.get("admin2"),
            "latitude": item.get("latitude"),
            "longitude": item.get("longitude"),
            "timezone": item.get("timezone"),
            "population": item.get("population"),
        }
        for item in payload.get("results", [])
        if item.get("country_code") == "IN"
    ]
    return {"source": "Open-Meteo Geocoding API", "places": results}


@router.get("/weather")
async def current_india_weather(
    latitude: float = Query(ge=6.0, le=38.0),
    longitude: float = Query(68.0, ge=68.0, le=98.0),
    place: str = Query(default="", max_length=160),
):
    payload = await fetch_json(
        "https://api.open-meteo.com/v1/forecast",
        {
            "latitude": latitude,
            "longitude": longitude,
            "current": "temperature_2m,relative_humidity_2m,apparent_temperature,precipitation,weather_code,wind_speed_10m",
            "timezone": "auto",
        },
    )
    return {
        "source": "Open-Meteo",
        "place": place,
        "latitude": payload.get("latitude", latitude),
        "longitude": payload.get("longitude", longitude),
        "timezone": payload.get("timezone"),
        "observed_at": payload.get("current", {}).get("time"),
        "fetched_at": datetime.now(timezone.utc).isoformat(),
        "current": payload.get("current", {}),
        "units": payload.get("current_units", {}),
    }
