import requests
import time
import os

SERVE_URL = os.environ.get("SERVE_URL", "http://my-housing-app-service/health")
INTERVAL = int(os.environ.get("INTERVAL_SECONDS", "10"))

while True:
    try:
        response = requests.get(SERVE_URL, timeout=5)
        print(f"[monitor] status={response.status_code} body={response.text}")
    except requests.exceptions.RequestException as e:
        print(f"[monitor] ERROR reaching {SERVE_URL}: {e}")
    time.sleep(INTERVAL)