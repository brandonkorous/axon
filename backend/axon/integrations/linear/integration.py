"""Linear integration — list, create, and update issues via GraphQL API."""

from __future__ import annotations

import json
from typing import Any

import httpx

from axon.integrations.base import BaseIntegration
from axon.integrations.linear.tools import LINEAR_TOOLS
from axon.logging import get_logger

logger = get_logger(__name__)

LINEAR_API_URL = "https://api.linear.app/graphql"


class LinearIntegration(BaseIntegration):
    """Linear integration using the GraphQL API."""

    name = "linear"
    description = "Linear — list issues, create issues, update issue status"
    required_scopes = ["read", "write"]
    tool_prefix = "linear_"

    def get_tools(self) -> list[dict[str, Any]]:
        return LINEAR_TOOLS

    async def execute(self, tool_name: str, arguments: str) -> str:
        try:
            args = json.loads(arguments)
        except json.JSONDecodeError:
            return f"Error: Invalid JSON arguments: {arguments}"

        handlers = {
            "linear_list_issues": self._list_issues,
            "linear_create_issue": self._create_issue,
            "linear_update_issue": self._update_issue,
        }

        handler = handlers.get(tool_name)
        if not handler:
            return f"Error: Unknown Linear tool: {tool_name}"

        api_key = self._credentials.get("api_key") or self._credentials.get("access_token", "")
        if not api_key:
            return "Error: Linear API key not configured. Add a Linear credential."

        try:
            return await handler(args, api_key)
        except httpx.HTTPStatusError as e:
            logger.exception("Linear API error: %s", tool_name)
            return f"Linear API error ({e.response.status_code}): {e.response.text[:200]}"
        except Exception as e:
            logger.exception("Linear error: %s", tool_name)
            return f"Error executing {tool_name}: {e}"

    async def _graphql(self, query: str, variables: dict, api_key: str) -> dict:
        """Execute a GraphQL query against the Linear API."""
        async with httpx.AsyncClient(timeout=15) as client:
            resp = await client.post(
                LINEAR_API_URL,
                json={"query": query, "variables": variables},
                headers={
                    "Authorization": api_key,
                    "Content-Type": "application/json",
                },
            )
            resp.raise_for_status()
            data = resp.json()

        if "errors" in data:
            error_msg = data["errors"][0].get("message", "Unknown GraphQL error")
            raise RuntimeError(f"Linear GraphQL error: {error_msg}")
        return data.get("data", {})

    async def _list_issues(self, args: dict, api_key: str) -> str:
        limit = args.get("limit", 20)
        filters: list[str] = []
        if args.get("status"):
            filters.append(f'state: {{ name: {{ eq: "{args["status"]}" }} }}')
        if args.get("assignee"):
            filters.append(f'assignee: {{ displayName: {{ contains: "{args["assignee"]}" }} }}')

        filter_str = ", ".join(filters)
        filter_arg = f", filter: {{ {filter_str} }}" if filter_str else ""

        query = f"""
        query ListIssues($limit: Int!) {{
            issues(first: $limit{filter_arg}, orderBy: updatedAt) {{
                nodes {{
                    identifier
                    title
                    state {{ name }}
                    priority
                    assignee {{ displayName }}
                    updatedAt
                }}
            }}
        }}
        """
        data = await self._graphql(query, {"limit": limit}, api_key)
        issues = data.get("issues", {}).get("nodes", [])

        if not issues:
            return "No issues found matching the filters."

        lines = []
        for issue in issues:
            assignee = issue.get("assignee", {})
            assignee_name = assignee.get("displayName", "Unassigned") if assignee else "Unassigned"
            state = issue.get("state", {}).get("name", "Unknown")
            lines.append(
                f"- **{issue['identifier']}** {issue['title']} "
                f"| {state} | {assignee_name} | P{issue.get('priority', 0)}"
            )
        return f"Found {len(issues)} issue(s):\n\n" + "\n".join(lines)

    async def _create_issue(self, args: dict, api_key: str) -> str:
        # First resolve team ID from key
        team_query = """
        query FindTeam($key: String!) {
            teams(filter: { key: { eq: $key } }) {
                nodes { id name }
            }
        }
        """
        team_data = await self._graphql(team_query, {"key": args["team_key"]}, api_key)
        teams = team_data.get("teams", {}).get("nodes", [])
        if not teams:
            return f"Error: Team with key '{args['team_key']}' not found."
        team_id = teams[0]["id"]

        variables: dict[str, Any] = {
            "title": args["title"],
            "teamId": team_id,
        }
        if args.get("description"):
            variables["description"] = args["description"]
        if args.get("priority") is not None:
            variables["priority"] = args["priority"]

        mutation = """
        mutation CreateIssue($title: String!, $teamId: String!, $description: String, $priority: Int) {
            issueCreate(input: {
                title: $title
                teamId: $teamId
                description: $description
                priority: $priority
            }) {
                issue { identifier title url }
            }
        }
        """
        data = await self._graphql(mutation, variables, api_key)
        issue = data.get("issueCreate", {}).get("issue", {})
        return f"Issue created: **{issue.get('identifier')}** — {issue.get('title')} ({issue.get('url', '')})"

    async def _update_issue(self, args: dict, api_key: str) -> str:
        issue_id = args["issue_id"]

        # Resolve issue UUID from identifier if needed
        resolve_query = """
        query FindIssue($id: String!) {
            issueSearch(query: $id, first: 1) {
                nodes { id identifier }
            }
        }
        """
        resolve_data = await self._graphql(resolve_query, {"id": issue_id}, api_key)
        issues = resolve_data.get("issueSearch", {}).get("nodes", [])
        if not issues:
            return f"Error: Issue '{issue_id}' not found."
        uuid = issues[0]["id"]

        input_fields: list[str] = []
        variables: dict[str, Any] = {"id": uuid}

        if args.get("status"):
            variables["stateId"] = args["status"]
            input_fields.append("stateId: $stateId")
        if args.get("priority") is not None:
            variables["priority"] = args["priority"]
            input_fields.append("priority: $priority")

        if not input_fields:
            return "Error: No fields to update. Provide status, assignee_email, or priority."

        mutation = f"""
        mutation UpdateIssue($id: String!{', $stateId: String' if 'stateId' in variables else ''}{', $priority: Int' if 'priority' in variables else ''}) {{
            issueUpdate(id: $id, input: {{ {', '.join(input_fields)} }}) {{
                issue {{ identifier title state {{ name }} }}
            }}
        }}
        """
        data = await self._graphql(mutation, variables, api_key)
        issue = data.get("issueUpdate", {}).get("issue", {})
        state = issue.get("state", {}).get("name", "")
        return f"Updated: **{issue.get('identifier')}** — {issue.get('title')} (now: {state})"
