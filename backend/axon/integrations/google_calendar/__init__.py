"""Google Calendar integration — register on import."""

from axon.integrations.google_calendar.integration import GoogleCalendarIntegration
from axon.integrations.registry import register_integration

register_integration("google_calendar", GoogleCalendarIntegration)
