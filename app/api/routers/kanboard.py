from fastapi import APIRouter, Response
import httpx
import logging
from app.core.config import settings

logger = logging.getLogger(__name__)
router = APIRouter()

@router.get("/auth")
async def get_kanboard_auth():
    """
    Attempts to perform a backend login to Kanboard using the configured credentials
    and returns a ready URL, or a token for the frontend to use.
    If the Kanboard instance simply supports passing credentials to its API, we can
    provide an authenticated URL if the UI supports it, or simply return the base URL.
    """
    kanboard_url = settings.KANBOARD_API_URL or "https://harvesthealth-kanboard.hf.space"

    if not settings.KANBOARD_USERNAME or not settings.KANBOARD_PASSWORD:
        logger.warning("Kanboard credentials missing. Returning base URL.")
        return {"url": kanboard_url, "status": "unauthenticated"}

    login_url = f"{kanboard_url}/api/login"

    try:
        # We supply the raw username and password to the frontend so it can perform a native
        # HTML form POST to the Kanboard UI login controller inside the iframe.
        # This bypasses the cross-origin cookie block that would happen if the backend authenticated.

        if settings.KANBOARD_USERNAME and settings.KANBOARD_PASSWORD:
            logger.info("Returning Kanboard credentials to frontend for UI iframe auto-login.")
            return {
                "url": kanboard_url,
                "status": "credentials_provided",
                "username": settings.KANBOARD_USERNAME,
                "password": settings.KANBOARD_PASSWORD
            }
        else:
            logger.warning("No Kanboard credentials available to return to frontend.")
            return {"url": kanboard_url, "status": "unauthenticated"}
    except Exception as e:
        logger.error(f"Error connecting to Kanboard auth: {e}")

    return {"url": kanboard_url, "status": "failed"}
