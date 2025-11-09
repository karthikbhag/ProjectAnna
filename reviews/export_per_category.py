#!/usr/bin/env python3
# export_per_category.py
# Read a topics_summary.json (from classify_dataset) and write one JSON per topic/category.

import json
from pathlib import Path
from collections import defaultdict
import argparse

def export_per_category(summary_path: str, outdir: str) -> None:
    summary = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    Path(outdir).mkdir(parents=True, exist_ok=True)

    buckets = defaultdict(list)
    for r in summary.get("classified_reviews", []):
        for t in r.get("matched_topics", []):
            buckets[t].append(r)

    for topic, reviews in buckets.items():
        out_file = Path(outdir) / f"{topic}_reviews.json"
        out_file.write_text(
            json.dumps({"category": topic, "count": len(reviews), "reviews": reviews}, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )
        print(f"Wrote {out_file} ({len(reviews)} rows)")

if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Export per-category review files from topics_summary.json")
    ap.add_argument("--summary", required=True, help="Path to topics_summary.json (from classify_dataset)")
    ap.add_argument("--outdir", required=True, help="Output directory for <category>_reviews.json files")
    args = ap.parse_args()

    export_per_category(args.summary, args.outdir)
