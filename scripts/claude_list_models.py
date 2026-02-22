import os
import sys
import json
import requests

API_KEY = os.environ.get("ANTHROPIC_API_KEY") or (len(sys.argv) > 1 and sys.argv[1])
if not API_KEY:
    print(
        "Usage: python list_models.py <sk-ant-...>  # or set ANTHROPIC_API_KEY in environment"
    )
    sys.exit(2)

r = requests.get(
    "https://api.anthropic.com/v1/models",
    headers={
        "x-api-key": API_KEY,
        "anthropic-version": "2023-06-01",
    },
    timeout=15,
)
print("HTTP", r.status_code)
print(json.dumps(r.json(), indent=2, ensure_ascii=False))
