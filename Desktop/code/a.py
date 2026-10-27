import time
import requests
from datetime import datetime

API_URL = "https://api.ltesocks.io/v2/port/reset/1580faab27891c539a97413875a51cfb631a14c25497a5079bf6dad8ad8a536d"
while True:
    now = datetime.now().strftime("%H:%M:%S")

    try:
        r = requests.get(API_URL, timeout=15)

        if r.ok:
            print(f"[{now}] SUCCESS - Proxy rotated | HTTP {r.status_code}")
        else:
            print(f"[{now}] FAILED  - HTTP {r.status_code} | {r.text[:100]}")

    except Exception as e:
        print(f"[{now}] FAILED  - {e}")

    time.sleep(60)

Cài 
