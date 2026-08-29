"""
Sensing Agent — Sense phase.

Collects raw Signals from GitHub and Linear. Supports live API calls
and --mock mode (reads from case file's mock_responses field).

Public interface:
    run(context: dict) -> dict
    context keys: case (full case dict), mock (bool)
    returns: {"signals": {"github": [...], "linear": [...]}}
"""

import os
import requests


class SystemConnectionError(Exception):
    def __init__(self, system: str, original: Exception):
        super().__init__(f"Failed to connect to System '{system}': {original}")
        self.system = system
        self.original = original


def _fetch_github_signals(repo_owner: str, repo_name: str) -> dict:
    token = os.environ["GITHUB_TOKEN"]
    headers = {"Authorization": f"Bearer {token}", "Accept": "application/vnd.github+json"}
    base = f"https://api.github.com/repos/{repo_owner}/{repo_name}"

    try:
        pulls = requests.get(f"{base}/pulls?state=closed&per_page=20", headers=headers, timeout=10)
        pulls.raise_for_status()

        issues = requests.get(f"{base}/issues?state=open&per_page=20", headers=headers, timeout=10)
        issues.raise_for_status()

        return {
            "merged_prs": [
                {"number": pr["number"], "title": pr["title"], "body": pr.get("body", ""), "merged_at": pr.get("merged_at")}
                for pr in pulls.json()
                if pr.get("merged_at")
            ],
            "open_issues": [
                {"number": i["number"], "title": i["title"], "labels": [l["name"] for l in i.get("labels", [])]}
                for i in issues.json()
                if "pull_request" not in i
            ],
        }
    except Exception as e:
        raise SystemConnectionError("GitHub", e)


def _fetch_linear_signals(team_id: str) -> dict:
    token = os.environ["LINEAR_API_KEY"]
    query = """
    query($teamId: String!) {
      issues(filter: { team: { id: { eq: $teamId } } }, first: 50) {
        nodes {
          id
          title
          state { name }
          updatedAt
          labels { nodes { name } }
        }
      }
    }
    """
    try:
        resp = requests.post(
            "https://api.linear.app/graphql",
            json={"query": query, "variables": {"teamId": team_id}},
            headers={"Authorization": token, "Content-Type": "application/json"},
            timeout=10,
        )
        resp.raise_for_status()
        data = resp.json()
        return {"tickets": data["data"]["issues"]["nodes"]}
    except Exception as e:
        raise SystemConnectionError("Linear", e)


def run(context: dict) -> dict:
    """
    Sense phase: collect raw Signals from GitHub and Linear.

    Args:
        context: {
            "case": <full case dict>,
            "mock": <bool>
        }

    Returns:
        {"signals": {"github": {...}, "linear": {...}}}
    """
    case = context["case"]
    mock = context.get("mock", False)

    if mock:
        return {"signals": case["mock_responses"]}

    config = case.get("live_config", {})
    github_signals = _fetch_github_signals(
        config.get("github_owner", ""),
        config.get("github_repo", ""),
    )
    linear_signals = _fetch_linear_signals(config.get("linear_team_id", ""))

    return {"signals": {"github": github_signals, "linear": linear_signals}}
