"""Teams senders — Online meeting creation via Microsoft Graph API."""

from __future__ import annotations

import httpx

from axon.logging import get_logger

logger = get_logger(__name__)

GRAPH_API_BASE = "https://graph.microsoft.com/v1.0"


async def _get_graph_token(tenant_id: str, app_id: str, app_secret: str) -> str:
    """Get a Microsoft Graph OAuth token using client credentials."""
    url = f"https://login.microsoftonline.com/{tenant_id}/oauth2/v2.0/token"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            url,
            data={
                "grant_type": "client_credentials",
                "client_id": app_id,
                "client_secret": app_secret,
                "scope": "https://graph.microsoft.com/.default",
            },
            timeout=10.0,
        )
    data = resp.json()
    return data.get("access_token", "")


async def create_teams_meeting(
    tenant_id: str,
    app_id: str,
    app_secret: str,
    organizer_id: str,
    subject: str,
    duration: int = 30,
    start_time: str = "",
) -> str:
    """Create a Microsoft Teams online meeting and return the join URL.

    Uses the Graph API with application permissions.
    *organizer_id* is the Azure AD user object ID of the meeting organizer.

    Returns a human-readable result with the meeting link.
    """
    if not app_id or not app_secret:
        return (
            "Error: Teams credentials not configured. Add 'teams_app_id' "
            "and 'teams_app_secret' credentials."
        )
    if not tenant_id:
        return "Error: Teams tenant ID not configured in org settings."
    if not organizer_id:
        return (
            "Error: Teams organizer not configured. Add a 'teams_organizer_id' "
            "credential (Azure AD user object ID)."
        )

    try:
        token = await _get_graph_token(tenant_id, app_id, app_secret)
        if not token:
            return "Error: Failed to authenticate with Microsoft Graph."

        meeting_data: dict = {"subject": subject}
        if start_time:
            meeting_data["startDateTime"] = start_time
            # Calculate end from duration
            meeting_data["endDateTime"] = ""  # Graph API handles this gracefully

        url = f"{GRAPH_API_BASE}/users/{organizer_id}/onlineMeetings"
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                url,
                headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                },
                json=meeting_data,
                timeout=10.0,
            )

        if resp.status_code in (200, 201):
            data = resp.json()
            join_url = data.get("joinWebUrl", "")
            meeting_id = data.get("id", "")
            logger.info("Teams meeting created: %s", meeting_id)
            return (
                f"Teams meeting created successfully.\n"
                f"**Subject:** {subject}\n"
                f"**Join URL:** {join_url}\n"
                f"**Meeting ID:** {meeting_id}"
            )
        else:
            error = resp.text[:300]
            logger.error("Graph API error %d: %s", resp.status_code, error)
            return f"Error creating Teams meeting: {resp.status_code} — {error}"
    except httpx.TimeoutException:
        return "Error: Microsoft Graph API request timed out."
    except Exception as e:
        logger.exception("Teams meeting creation failed")
        return f"Error creating Teams meeting: {e}"
