"""COMMS_TOOLS — tool schemas for agent communication (email, Discord, contacts)."""

from __future__ import annotations

from typing import Any


COMMS_TOOLS: list[dict[str, Any]] = [
    {
        "type": "function",
        "function": {
            "name": "comms_send_email",
            "description": (
                "Send an email on behalf of this agent. The email will be queued "
                "for user approval before sending (unless approval is disabled). "
                "Use comms_lookup_contact first to resolve the recipient's email address.\n\n"
                "EMAIL FORMAT RULES:\n"
                "- Write the body as HTML using <p> tags for each paragraph.\n"
                "- Structure: greeting paragraph, 1-3 body paragraphs, closing paragraph.\n"
                "- Keep paragraphs short (2-3 sentences max).\n"
                "- Do NOT include your name/title/signature — it is appended automatically.\n"
                "- Do NOT use <html>, <head>, or <body> wrapper tags — just the inner content.\n"
                "- Use <a> for links, <strong> for emphasis. No inline styles.\n"
                "- Tone: professional, concise, human. Not robotic, not marketing-speak."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "to": {
                        "type": "string",
                        "description": "Recipient email address",
                    },
                    "subject": {
                        "type": "string",
                        "description": "Email subject line",
                    },
                    "body": {
                        "type": "string",
                        "description": "Email body content (plain text or HTML)",
                    },
                    "cc": {
                        "type": "string",
                        "description": "CC recipient email address (optional)",
                    },
                },
                "required": ["to", "subject", "body"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comms_send_discord",
            "description": (
                "Send a Discord message on behalf of this agent. The message will be "
                "queued for user approval before sending (unless approval is disabled)."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "target": {
                        "type": "string",
                        "description": "Discord user ID or channel ID to send to",
                    },
                    "content": {
                        "type": "string",
                        "description": "Message content",
                    },
                    "is_dm": {
                        "type": "boolean",
                        "description": "True to send as a DM, false for channel message (default: false)",
                    },
                },
                "required": ["target", "content"],
            },
        },
    },
    {
        "type": "function",
        "function": {
            "name": "comms_lookup_contact",
            "description": (
                "Look up a contact by name, email, role, or other attributes. "
                "Returns matching contacts with their communication details."
            ),
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Search query — name, email, role, or company",
                    },
                },
                "required": ["query"],
            },
        },
    },
]
