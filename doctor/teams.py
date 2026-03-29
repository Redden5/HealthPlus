"""
Microsoft Graph API — Teams online meeting creation.

Required environment variables:
    MS_TENANT_ID        Azure AD tenant ID
    MS_CLIENT_ID        App (client) ID
    MS_CLIENT_SECRET    Client secret value
    MS_ORGANIZER_EMAIL  Email of the licensed M365 user who organises meetings

If any variable is missing the function returns a placeholder URL so the rest
of the feature still works during development without Azure credentials.
"""

import os
import logging
from datetime import timedelta

logger = logging.getLogger(__name__)

GRAPH_BASE = "https://graph.microsoft.com/v1.0"
TOKEN_URL = "https://login.microsoftonline.com/{tenant}/oauth2/v2.0/token"


def _get_access_token(tenant_id, client_id, client_secret):
    """Obtain an app-only access token using the client-credentials flow."""
    import urllib.request
    import urllib.parse
    import json

    data = urllib.parse.urlencode({
        "grant_type":    "client_credentials",
        "client_id":     client_id,
        "client_secret": client_secret,
        "scope":         "https://graph.microsoft.com/.default",
    }).encode()

    req = urllib.request.Request(
        TOKEN_URL.format(tenant=tenant_id),
        data=data,
        method="POST",
    )
    req.add_header("Content-Type", "application/x-www-form-urlencoded")

    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["access_token"]


def create_teams_meeting(title, scheduled_at):
    """
    Create a Teams online meeting via Microsoft Graph and return
    (join_url, teams_meeting_id).

    Falls back to ('', '') if Azure env vars are not configured.
    """
    tenant_id     = os.getenv("MS_TENANT_ID")
    client_id     = os.getenv("MS_CLIENT_ID")
    client_secret = os.getenv("MS_CLIENT_SECRET")
    organizer     = os.getenv("MS_ORGANIZER_EMAIL")

    if not all([tenant_id, client_id, client_secret, organizer]):
        logger.warning("MS Graph env vars not set — skipping Teams meeting creation.")
        return "", ""

    import urllib.request
    import json

    try:
        token = _get_access_token(tenant_id, client_id, client_secret)

        end_time = scheduled_at + timedelta(hours=1)
        body = json.dumps({
            "subject": title,
            "startDateTime": scheduled_at.strftime("%Y-%m-%dT%H:%M:%S"),
            "endDateTime":   end_time.strftime("%Y-%m-%dT%H:%M:%S"),
        }).encode()

        url = f"{GRAPH_BASE}/users/{urllib.parse.quote(organizer)}/onlineMeetings"
        req = urllib.request.Request(url, data=body, method="POST")
        req.add_header("Authorization", f"Bearer {token}")
        req.add_header("Content-Type", "application/json")

        with urllib.request.urlopen(req) as resp:
            result = json.loads(resp.read())
            return result.get("joinWebUrl", ""), result.get("id", "")

    except Exception as exc:
        logger.error("Teams meeting creation failed: %s", exc)
        return "", ""
