import httpx
from app.core.config import settings

def get_secret(key_name: str):
    # This is a stub for getting a secret from the HF space environment or via HF API.
    # In a real deployed Hugging Face Space, secrets are mounted as environment variables.
    import os
    env_val = os.getenv(key_name)
    if env_val:
        return env_val

    # If not in env, we could theoretically fetch from HF API if authorized.
    url = f"https://huggingface.co/api/spaces/harvesthealth/ImmoTelegram/secrets/{key_name}"
    headers = {
        "Authorization": f"Bearer {settings.HF_TOKEN}"
    }

    try:
        if settings.HF_TOKEN:
            res = httpx.get(url, headers=headers, timeout=5.0)
            res.raise_for_status()
            # Depending on API format, parse the secret value
            return res.json().get("value", f"mock-{key_name}")
    except Exception as e:
        print(f"HF Vault fetch failed for {key_name}: {e}")

    return f"mock-{key_name}"
