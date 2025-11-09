# reviews/geocode_utils.py
# pip install geopy certifi
from typing import Optional, Tuple
import time, ssl, certifi
from geopy.geocoders import Nominatim

_context = ssl.create_default_context(cafile=certifi.where())
_geocoder = Nominatim(user_agent="tmobile_topics_geocoder", ssl_context=_context)
_CACHE: dict[str, Tuple[float, float]] = {}

def get_coordinates(city: str, state: str) -> Optional[Tuple[float, float]]:
    key = f"{city}, {state}"
    if key in _CACHE:
        return _CACHE[key]
    try:
        loc = _geocoder.geocode(key, timeout=30)
        if loc:
            _CACHE[key] = (loc.latitude, loc.longitude)
            return _CACHE[key]
    except Exception:
        pass
    return None

def enrich_dataset_with_city_coords(dataset: dict, delay: float = 1.0) -> dict:
    for st in dataset.get("states", []):
        sname = st.get("state")
        for c in st.get("cities", []):
            cname = c.get("city")
            coords = get_coordinates(cname, sname)
            if coords:
                lat, lon = coords
                c["city_lat"] = lat
                c["city_lon"] = lon
            time.sleep(delay)
    return dataset
