"""Small free public-data access probes; save exact bytes and provenance."""
import sys
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import digest, now_utc, write_json

targets = [
    ("alfred_gdp_20200430.csv", "https://alfred.stlouisfed.org/graph/alfredgraph.csv?" + urlencode({"id": "A191RL1Q225SBEA", "vintage_date": "2020-04-30", "cosd": "2019-01-01", "coed": "2020-12-31"})),
    ("alfred_gdp_20200529.csv", "https://alfred.stlouisfed.org/graph/alfredgraph.csv?" + urlencode({"id": "A191RL1Q225SBEA", "vintage_date": "2020-05-29", "cosd": "2019-01-01", "coed": "2020-12-31"})),
    ("gdelt_20200615160000.zip", "https://data.gdeltproject.org/gdeltv2/20200615160000.gkg.csv.zip"),
    ("gdelt_20260615160000.zip", "https://data.gdeltproject.org/gdeltv2/20260615160000.gkg.csv.zip"),
]


def main():
    folder = ROOT / "data/raw/history_probe"
    folder.mkdir(parents=True, exist_ok=True)
    results = []
    for name, url in targets:
        row = {"name": name, "url": url, "retrieved_at": now_utc()}
        path = folder / name
        try:
            if path.exists():
                data = path.read_bytes()
                row["cache_hit"] = True
            else:
                with urlopen(Request(url, headers={"User-Agent": "ConsumerSentimentResearch/0.1"}), timeout=35) as response:
                    data = response.read(20_000_001)
                if len(data) > 20_000_000:
                    raise ValueError("Response exceeds 20 MB probe cap")
                path.write_bytes(data)
            row.update(status="downloaded", bytes=len(data), sha256=digest(data))
            if name.endswith(".csv"):
                row["csv_preview"] = data.decode("utf-8-sig").splitlines()[:8]
        except (HTTPError, URLError, TimeoutError, ValueError) as exc:
            row.update(status="failed", error=str(exc))
        results.append(row)
        print(row, flush=True)
        write_json(folder / "manifest.json", results)


if __name__ == "__main__":
    main()
