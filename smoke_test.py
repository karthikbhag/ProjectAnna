# smoke_test.py
import json
from pathlib import Path
from collections import defaultdict

# Import classifier only (no geocoding)
from reviews.tmobile_topics import classify_review, classify_dataset

# 1) Quick single-text check
print("Single review classify:",
      classify_review("Speeds were slow, latency spiked, then it dropped connection."))

# 2) Load dataset
data_path = Path("reviews/data/tmobile_reviews.json")
if not data_path.exists():
    raise FileNotFoundError(f"Could not find {data_path}. Put your JSON there or change the path.")
data = json.loads(data_path.read_text(encoding="utf-8"))

# 3) Classify (no filters)
result = classify_dataset(data)

# 4) Write topics_summary.json (single write)
out_summary = Path("reviews/data/topics_summary.json")
out_summary.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
print(f"Wrote summary → {out_summary.resolve()}")

# 5) Export one JSON per topic
def write_per_category_files(summary: dict, outdir: str):
    outdir_path = Path(outdir)
    outdir_path.mkdir(parents=True, exist_ok=True)
    buckets = defaultdict(list)
    for r in summary.get("classified_reviews", []):
        for t in r.get("matched_topics", []):
            buckets[t].append(r)
    for topic, reviews in buckets.items():
        out_file = outdir_path / f"{topic}_reviews.json"
        out_file.write_text(
            json.dumps({"category": topic, "count": len(reviews), "reviews": reviews},
                       indent=2, ensure_ascii=False),
            encoding="utf-8"
        )
        print(f"Wrote {out_file} ({len(reviews)} rows)")

write_per_category_files(result, "reviews/data/out")

# 6) Minimal stats
print("Total reviews classified:", result["meta"]["total_reviews_classified"])
print("Top 10 topics overall:",
      sorted(result["topic_counts_overall"].items(), key=lambda x: -x[1])[:10])


# import json
# from pathlib import Path

# # 1) import the classifier module
# from reviews.tmobile_topics import classify_review, classify_dataset
# from reviews.geocode_utils import enrich_dataset_with_city_coords


# # 2) quick single-text smoke check
# print("Single review classify:", classify_review("Speeds were slow, latency spiked, then it dropped connection."))

# # 3) load your dataset
# data_path = Path("reviews/data/tmobile_reviews.json")
# if not data_path.exists():
#     raise FileNotFoundError(f"Could not find {data_path}. Put your JSON there or change the path.")

# data = json.loads(data_path.read_text(encoding="utf-8"))

# # 4) run the classifier on the dataset (no filters)
# result = classify_dataset(data)

# # 1) Write the main summary
# from pathlib import Path
# import json
# out_summary = Path("reviews/data/topics_summary.json")
# out_summary.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
# print(f"Wrote summary → {out_summary.resolve()}")

# # 2) Immediately export one JSON per topic
# from collections import defaultdict

# def write_per_category_files(summary: dict, outdir: str):
#     outdir_path = Path(outdir)
#     outdir_path.mkdir(parents=True, exist_ok=True)

#     buckets = defaultdict(list)
#     for r in summary.get("classified_reviews", []):
#         for t in r.get("matched_topics", []):
#             buckets[t].append(r)

#     for topic, reviews in buckets.items():
#         out_file = outdir_path / f"{topic}_reviews.json"
#         out_file.write_text(
#             json.dumps({"category": topic, "count": len(reviews), "reviews": reviews},
#                        indent=2, ensure_ascii=False),
#             encoding="utf-8"
#         )
#         print(f"Wrote {out_file} ({len(reviews)} rows)")

# # call it right away
# write_per_category_files(result, "reviews/data/out")
# # 5) print minimal sanity info
# print("Total reviews classified:", result["meta"]["total_reviews_classified"])
# print("Top 10 topics overall:", sorted(result["topic_counts_overall"].items(), key=lambda x: -x[1])[:10])

# # 6) write a summary file to inspect manually or use in UI
# out = Path("reviews/data/topics_summary.json")
# out.write_text(json.dumps(result, indent=2, ensure_ascii=False), encoding="utf-8")
# print(f"Wrote summary → {out.resolve()}")

# data_path = Path("reviews/data/tmobile_reviews.json")
# data = json.loads(data_path.read_text(encoding="utf-8"))

# # add geocoordinates once
# data = enrich_dataset_with_city_coords(data, delay=1.0)

# # now classify as usual
# summary = classify_dataset(data)
# Path("reviews/data/topics_summary.json").write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")