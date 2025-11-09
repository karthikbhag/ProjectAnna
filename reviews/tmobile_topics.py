# tmobile_topics.py
import json
from pathlib import Path
from collections import Counter, defaultdict
from typing import Any, Dict, List, Optional, Tuple
import time, ssl, certifi
from geopy.geocoders import Nominatim

# -----------------------------
# Keywords / classification
# -----------------------------
DEFAULT_KEYWORDS: Dict[str, List[str]] = {
    # network & performance
    "bandwidth":   ["bandwidth", "throughput", "capacity", "congestion", "data cap", "cap"],
    "reliability": ["reliability", "reliable", "uptime", "outage", "crash", "disconnect", "drop", "packet loss", "stability"],
    "latency":     ["latency", "ping", "delay", "lag", "jitter", "response time"],
    "coverage":    ["coverage", "signal", "bars", "dead zone", "5g", "lte"],
    "speed":       ["speed", "download", "upload", "fast", "slow"],
    # plans & billing
    "billing":     ["bill", "billing", "charged", "charge", "fee", "fees", "price", "pricing"],
    "promotion":   ["promo", "promotion", "trade-in", "trade in", "discount", "deal"],
    "plan_change": ["plan", "plan change", "add a line", "upgrade plan", "downgrade"],
    # device & services
    "upgrade":       ["upgrade", "new phone", "swap", "trade-in"],
    "repair":        ["repair", "replacement", "fix", "warranty", "broken", "screen"],
    "accessories":   ["case", "charger", "screen protector", "accessory", "accessories"],
    "hotspot":       ["hotspot", "tether"],
    "esim":          ["esim", "e-sim"],
    "wifi_calling":  ["wifi calling", "wi-fi calling", "wificalling"],
    "spam_blocking": ["spam", "blocking", "scam shield"],
    # store logistics & CX
    "inventory":   ["stock", "in stock", "out of stock", "inventory"],
    "parking":     ["parking", "lot", "garage", "valet"],
    "customer_service": ["staff", "rep", "representative", "helpful", "rude", "attitude", "polite", "knowledgeable"],
    "communication":    ["communication", "explain", "explained", "clarity", "confusing", "confusion", "told", "said"],
    "checkout":         ["checkout", "register", "pos", "point of sale", "ring up"],
    # catch-all
    "experience":  ["experience", "overall", "visit", "store"],
}

def _norm(s: str) -> str:
    return (s or "").lower()

def classify_review(text: str, keywords: Optional[Dict[str, List[str]]] = None) -> List[str]:
    kws = keywords or DEFAULT_KEYWORDS
    t = _norm(text)
    hits = [topic for topic, terms in kws.items() if any(term in t for term in terms)]
    return sorted(set(hits)) or ["other"]

def _iter_reviews(dataset: Dict[str, Any]):
    # expects: dataset["states"][i]["cities"][j]["stores"][k]["reviews"]
    for st in dataset.get("states", []):
        state = st.get("state")
        for c in st.get("cities", []):
            city = c.get("city")
            for s in c.get("stores", []):
                store_meta = {
                    "store_id": s.get("store_id"),
                    "store_name": s.get("store_name"),
                    "address": s.get("address"),
                    "city": s.get("city"),
                    "state": s.get("state"),
                }
                for r in s.get("reviews", []):
                    yield state, city, store_meta, r

# -----------------------------
# Geocoding (Option A)
# -----------------------------
_context = ssl.create_default_context(cafile=certifi.where())
_geocoder = Nominatim(user_agent="tmobile_topics_geocoder", ssl_context=_context)
_GEOCACHE: Dict[str, Tuple[float, float]] = {}

def get_coordinates(city: str, state: str) -> Optional[Tuple[float, float]]:
    """Return (lat, lon) for 'City, State' or None if not found."""
    key = f"{city}, {state}"
    if key in _GEOCACHE:
        return _GEOCACHE[key]
    try:
        loc = _geocoder.geocode(key, timeout=30)
        if loc:
            _GEOCACHE[key] = (loc.latitude, loc.longitude)
            return _GEOCACHE[key]
    except Exception:
        pass
    return None

def enrich_dataset_with_city_coords(dataset: dict, delay: float = 1.0) -> dict:
    """
    Attach 'city_lat' and 'city_lon' to each city entry (first call will hit API, subsequent runs use cache).
    WARNING: Nominatim has rate-limits; keep delay>=1s if doing many cities.
    """
    for st in dataset.get("states", []):
        state_name = st.get("state")
        for c in st.get("cities", []):
            city_name = c.get("city")
            coords = get_coordinates(city_name, state_name)
            if coords:
                lat, lon = coords
                c["city_lat"] = lat
                c["city_lon"] = lon
            time.sleep(delay)
    return dataset

# -----------------------------
# Classification API
# -----------------------------
def classify_dataset(
    dataset: Dict[str, Any],
    *,
    keywords: Optional[Dict[str, List[str]]] = None,
    min_rating: int = 1,
    max_rating: int = 5,
    sentiment: str = "any",         # any|positive|negative|neutral
    state_filter: Optional[str] = None,
    city_filter: Optional[str] = None,
) -> Dict[str, Any]:
    kws = keywords or DEFAULT_KEYWORDS
    topic_counts = Counter()
    by_state = defaultdict(Counter)
    by_city = defaultdict(Counter)
    by_store = defaultdict(Counter)
    rows: List[Dict[str, Any]] = []

    for state, city, store, r in _iter_reviews(dataset):
        if state_filter and state != state_filter: continue
        if city_filter and city != city_filter:   continue

        rating = int(r.get("rating", 0))
        sent = _norm(r.get("sentiment", ""))
        if not (min_rating <= rating <= max_rating): continue
        if sentiment != "any" and sent != sentiment: continue

        blob = f"{r.get('title','')} {r.get('text','')}"
        topics = classify_review(blob, kws)

        rows.append({
            "state": state,
            "city": city,
            "store_id": store["store_id"],
            "store_name": store["store_name"],
            "address": store["address"],
            "rating": rating,
            "sentiment": sent or "unknown",
            "title": r.get("title", ""),
            "text": r.get("text", ""),
            "date": r.get("date", ""),
            "matched_topics": topics,
        })
        for t in topics:
            topic_counts[t] += 1
            by_state[state][t] += 1
            by_city[(state, city)][t] += 1
            by_store[store["store_id"]][t] += 1

    # Optional: pass city coords through to the summary (handy for frontend maps)
    city_coords = {}
    for st in dataset.get("states", []):
        sname = st.get("state")
        for c in st.get("cities", []):
            cname = c.get("city")
            lat = c.get("city_lat"); lon = c.get("city_lon")
            if lat is not None and lon is not None:
                city_coords[f"{sname}::{cname}"] = {"lat": lat, "lon": lon}

    return {
        "meta": {
            "filters": {
                "min_rating": min_rating, "max_rating": max_rating,
                "sentiment": sentiment, "state": state_filter, "city": city_filter,
            },
            "total_reviews_classified": len(rows),
        },
        "topic_counts_overall": dict(topic_counts),
        "by_state": {st: dict(cnts) for st, cnts in by_state.items()},
        "by_city": {f"{st} :: {cty}": dict(cnts) for (st, cty), cnts in by_city.items()},
        "by_store": {sid: dict(cnts) for sid, cnts in by_store.items()},
        "city_coords": city_coords,            # <-- now included
        "classified_reviews": rows,
    }

# -----------------------------
# Script-style usage (runs when you execute this file)
# -----------------------------
if __name__ == "__main__":
    # 1) Load dataset
    data_path = Path("reviews/data/tmobile_reviews.json")
    if not data_path.exists():
        raise FileNotFoundError(f"Could not find {data_path}. Put your JSON there or change the path.")
    DATA = json.loads(data_path.read_text(encoding="utf-8"))

    # 2) Enrich with coordinates FIRST
    DATA = enrich_dataset_with_city_coords(DATA, delay=1.0)

    # 3) Classify
    result = classify_dataset(
        DATA,
        sentiment="any",
        min_rating=1,
        max_rating=5,
        state_filter=None,
        city_filter=None,
    )

    # 4) Write summary
    out_summary = Path("reviews/data/topics_summary.json")
    out_summary.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
    print(f"Wrote {out_summary.resolve()}")

    # 5) Optional: per-topic files
    from collections import defaultdict
    outdir = Path("reviews/data/out")
    outdir.mkdir(parents=True, exist_ok=True)
    buckets = defaultdict(list)
    for r in result.get("classified_reviews", []):
        for t in r.get("matched_topics", []):
            buckets[t].append(r)
    for topic, reviews in buckets.items():
        (outdir / f"{topic}_reviews.json").write_text(
            json.dumps({"category": topic, "count": len(reviews), "reviews": reviews},
                       indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"Wrote {outdir / f'{topic}_reviews.json'} ({len(reviews)} rows)")
