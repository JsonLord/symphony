import requests
import time

base_url = "https://harvesthealth-immotelegram.hf.space"
use_case_prompt = "Build a Gradio app around https://github.com/HKUDS/CLI-Anything.git Expose API endpoints and deploy with SDK Gradio to Huggingface space harvesthealth/dashboard1 Via Jules agent profile harvesthealth"

def test_usecase():
    print(f"--- 1. Creating Profile 'harvesthealth' ---")
    res = requests.post(f"{base_url}/api/v1/settings/profiles", json={
        "profile_name": "harvesthealth",
        "parameters": {}
    })
    print(f"Status: {res.status_code}")
    if res.status_code != 200:
        print("Failed to create profile.")
        return
    profile_id = res.json().get("profile_id")
    print(f"Profile ID: {profile_id}\n")

    print(f"--- 2. Creating Project with Prompt ---")
    res = requests.post(f"{base_url}/api/v1/projects/", json={
        "title": "CLI-Anything Gradio App",
        "description": use_case_prompt,
        "profile_id": profile_id
    })
    print(f"Status: {res.status_code}")
    print(f"Body: {res.text}\n")
    if res.status_code == 200:
        project_id = res.json().get("project_id")

        print(f"--- 3. Testing Stream for Project {project_id} ---")
        try:
            res = requests.post(f"{base_url}/api/v1/stream", json={
                "message": use_case_prompt,
                "forward_to_telegram": False,
                "project_id": project_id
            }, stream=True)
            print(f"Stream Status: {res.status_code}")

            lines_read = 0
            for line in res.iter_lines():
                if line:
                    print(f"Stream Chunk: {line.decode('utf-8')}")
                    lines_read += 1
                if lines_read > 5:
                    break
        except Exception as e:
            print(f"Stream error: {e}")

if __name__ == "__main__":
    test_usecase()
