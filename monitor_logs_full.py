import subprocess
import time
import os
import json

token = os.environ.get("HF_TOKEN")
if not token:
    print("HF_TOKEN missing in env, cannot monitor")
    exit(1)

url = "https://huggingface.co/api/spaces/harvesthealth/ImmoTelegram/logs/run"
print(f"Fetching recent logs for project creation...")
try:
    proc = subprocess.run(["curl", "-s", "-H", f"Authorization: Bearer {token}", url], capture_output=True, text=True)
    lines = proc.stdout.split("\n")

    # We want to trace the logs for project creation which happened ~1 minute ago
    for line in lines[-80:]:
        if "data:" in line:
            try:
                raw_data = line.split("data: ", 1)[1]
                parsed = json.loads(raw_data)
                text = parsed.get("data", "").strip()
                if text:
                    print("LOG:", text)
            except:
                pass
except Exception as e:
    print("Error monitoring:", e)
