"""Read DeepSeek model availability and balance without exposing credentials."""
import json
import os
import sys
from pathlib import Path
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
from sentiment_project.common import load_local_env, now_utc, read_json, write_json


def main():
    load_local_env()
    cfg = read_json(ROOT / "configs/deepseek.json")
    key = os.getenv(cfg["api_key_env"])
    if not key:
        raise ValueError("DeepSeek credential not configured")
    result = {"checked_at": now_utc()}
    for endpoint, label in [("/models", "models"), ("/user/balance", "balance")]:
        request = Request(cfg["base_url"] + endpoint, headers={"Authorization": "Bearer " + key})
        try:
            with urlopen(request, timeout=30) as response:
                body = json.loads(response.read().decode("utf-8"))
            if label == "models":
                result[label] = [m["id"] for m in body.get("data", [])]
                result["configured_models_available"] = all(m in result[label] for m in cfg["roles"].values())
            else:
                result[label] = {"is_available": body.get("is_available"), "balance_infos": [
                    {k: entry.get(k) for k in ["currency", "total_balance", "granted_balance", "topped_up_balance"]}
                    for entry in body.get("balance_infos", [])]}
        except HTTPError as exc:
            result[label] = {"http_status": exc.code}
        except (URLError, TimeoutError):
            result[label] = {"error": "network_unavailable"}
    write_json(ROOT / "data/private/deepseek_preflight.json", result)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
