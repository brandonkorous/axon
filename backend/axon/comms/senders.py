"""Comms senders — actual API calls to Resend and Discord."""

from __future__ import annotations

import logging

import httpx

logger = logging.getLogger(__name__)

EMAIL_TEMPLATE = """\
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="margin:0;padding:0;background:#efe8de;">
  <div style="max-width:600px;margin:24px auto;padding:32px 28px;
              background:#faf8f5;border-radius:12px;
              font-family:'DM Sans',-apple-system,BlinkMacSystemFont,'Segoe UI',Roboto,sans-serif;
              font-size:15px;line-height:1.6;color:#37332e;">
    {body}
    {signature}
  </div>
</body>
</html>"""


def _wrap_email(body: str, signature: str = "") -> str:
    """Wrap email body in a clean HTML template."""
    sig_html = ""
    if signature:
        sig_html = (
            f'<div style="margin-top:24px;padding-top:16px;'
            f'border-top:1px solid #d5cdc2;color:#8a8279;font-size:13px;">'
            f"{signature}</div>"
        )
    return EMAIL_TEMPLATE.format(body=body, signature=sig_html)


async def send_email(
    api_key: str,
    email_domain: str,
    to: str,
    subject: str,
    body: str,
    cc: str = "",
    from_name: str = "",
    signature: str = "",
    agent_display_name: str = "",
) -> str:
    """Send an email via the Resend API.

    From address: {from_name}@{email_domain}.
    If *signature* is provided it is appended to the HTML body.
    Returns a human-readable result string.
    """
    if not api_key:
        return "Error: Resend API key not configured. Add a 'resend' credential in org settings."

    if not email_domain:
        return "Error: Email domain not configured in org comms settings."

    from_addr = f"{from_name}@{email_domain}" if from_name else f"axon@{email_domain}"

    sig_text = ""
    if signature:
        sig_text = signature.replace("{{agent_name}}", agent_display_name or from_name)
        sig_text = sig_text.replace("\n", "<br/>")
    html = _wrap_email(body, sig_text)

    payload: dict = {
        "from": from_addr,
        "to": [to],
        "subject": subject,
        "html": html,
    }
    if cc:
        payload["cc"] = [cc]

    try:
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                "https://api.resend.com/emails",
                headers={"Authorization": f"Bearer {api_key}"},
                json=payload,
                timeout=15.0,
            )
        if resp.status_code in (200, 201):
            data = resp.json()
            logger.info("Email sent to %s (id: %s)", to, data.get("id"))
            return f"Email sent to {to} successfully."
        else:
            error = resp.text[:300]
            logger.error("Resend API error %d: %s", resp.status_code, error)
            return f"Error sending email: {resp.status_code} — {error}"
    except httpx.TimeoutException:
        return "Error: Resend API request timed out."
    except Exception as e:
        logger.exception("Email send failed")
        return f"Error sending email: {e}"


async def send_discord_message(
    bot_token: str,
    target: str,
    content: str,
    is_dm: bool = False,
) -> str:
    """Send a Discord message via REST API.

    Returns a human-readable result string.
    """
    if not bot_token:
        return "Error: Discord bot token not configured. Add a 'discord' credential in org settings."

    headers = {"Authorization": f"Bot {bot_token}", "Content-Type": "application/json"}

    try:
        async with httpx.AsyncClient() as client:
            if is_dm:
                dm_resp = await client.post(
                    "https://discord.com/api/v10/users/@me/channels",
                    headers=headers,
                    json={"recipient_id": target},
                    timeout=10.0,
                )
                if dm_resp.status_code != 200:
                    return f"Error creating DM channel: {dm_resp.status_code}"
                channel_id = dm_resp.json()["id"]
            else:
                channel_id = target

            resp = await client.post(
                f"https://discord.com/api/v10/channels/{channel_id}/messages",
                headers=headers,
                json={"content": content},
                timeout=10.0,
            )

        if resp.status_code == 200:
            logger.info("Discord message sent to %s", target)
            return f"Discord message sent to {'DM ' if is_dm else 'channel '}{target}."
        else:
            error = resp.text[:300]
            logger.error("Discord API error %d: %s", resp.status_code, error)
            return f"Error sending Discord message: {resp.status_code} — {error}"
    except httpx.TimeoutException:
        return "Error: Discord API request timed out."
    except Exception as e:
        logger.exception("Discord send failed")
        return f"Error sending Discord message: {e}"
