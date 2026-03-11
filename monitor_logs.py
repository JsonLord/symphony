import subprocess
import time
import os

token = os.environ.get("HF_TOKEN")
if not token:
    print("HF_TOKEN missing in env, cannot monitor")
    exit(1)

url = "https://huggingface.co/api/spaces/harvesthealth/ImmoTelegram/logs/run"
print(f"Fetching recent logs...")
try:
    # Just run a quick curl to see the past minute's logs since we just ran the use case
    proc = subprocess.run(["curl", "-s", "-H", f"Authorization: Bearer {token}", url], capture_output=True, text=True)
    lines = proc.stdout.split("\n")
    # Display the last 30 lines
    for line in lines[-30:]:
        if "data:" in line:
            # Clean up the SSE JSON wrapper a bit for readability
            import json
            try:
                raw_data = line.split("data: ", 1)[1]
                parsed = json.loads(raw_data)
                print("LOG:", parsed.get("data", "").strip())
            except:
                print("RAW:", line)
except Exception as e:
    print("Error monitoring:", e)
