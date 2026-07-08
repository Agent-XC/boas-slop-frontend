"""GitHub failure-issue adapter: opens/reuses/closes a scraper-failure-
labeled issue based on the pipeline's abort_reason, so the weekly job never
silently commits a suspicious result without also surfacing why.

decide_action() is pure and unit tested directly (see tests/test_failure_issue.py).
GitHubIssueClient's HTTP-calling methods are deliberately not covered by the
routine fixture-based suite, per issue #5's acceptance criteria — verify
those with a one-off manual smoke test against the real repo instead,
the same way pipeline/fetch.py's live-network calls are handled.
"""

from dataclasses import dataclass
from enum import Enum

import requests

FAILURE_LABEL = "scraper-failure"
_API_BASE = "https://api.github.com"


class Action(Enum):
    CREATE = "create"
    COMMENT = "comment"
    CLOSE = "close"
    NOOP = "noop"


def decide_action(existing_open_issue: int | None, abort_reason: str | None) -> Action:
    """Decides what to do with the scraper-failure issue.

    abort_reason is None for both a successful commit and a clean
    no-change run (see pipeline.core.run_pipeline) — neither is a failure,
    so both should close an open issue rather than create/comment.
    """
    if abort_reason:
        return Action.COMMENT if existing_open_issue is not None else Action.CREATE
    return Action.CLOSE if existing_open_issue is not None else Action.NOOP


@dataclass
class GitHubIssueClient:
    repo: str
    token: str

    def _headers(self) -> dict:
        return {"Authorization": f"Bearer {self.token}", "Accept": "application/vnd.github+json"}

    def _request(self, method: str, path: str, **kwargs) -> requests.Response:
        response = requests.request(method, f"{_API_BASE}{path}", headers=self._headers(), timeout=30, **kwargs)
        response.raise_for_status()
        return response

    def find_open_failure_issue(self) -> int | None:
        """Looks up the currently open scraper-failure issue, if any.

        Note (verified during issue #5's manual smoke test): GitHub's
        labels+state filtered issue list has a few seconds of eventual-
        consistency lag right after a create/close. Harmless here — this
        is only ever called once at the start of a run, checking for an
        issue left open by a *previous* run, never immediately after this
        same run's own create/close.
        """
        issues = self._request(
            "GET", f"/repos/{self.repo}/issues", params={"labels": FAILURE_LABEL, "state": "open"}
        ).json()
        return issues[0]["number"] if issues else None

    def ensure_label_exists(self) -> None:
        response = requests.get(
            f"{_API_BASE}/repos/{self.repo}/labels/{FAILURE_LABEL}", headers=self._headers(), timeout=30
        )
        if response.status_code == 404:
            self._request(
                "POST",
                f"/repos/{self.repo}/labels",
                json={
                    "name": FAILURE_LABEL,
                    "color": "d73a4a",
                    "description": (
                        "The automated catalogue pipeline aborted a run without committing; "
                        "see the issue body for why."
                    ),
                },
            )
        else:
            response.raise_for_status()

    def create_failure_issue(self, abort_reason: str) -> int:
        self.ensure_label_exists()
        response = self._request(
            "POST",
            f"/repos/{self.repo}/issues",
            json={
                "title": "Pipeline aborted: suspicious scrape result",
                "body": (
                    "The automated catalogue pipeline aborted this run without committing.\n\n"
                    f"**Reason:** {abort_reason}\n\n"
                    "Existing `data.json`/`changelog.json` were left untouched."
                ),
                "labels": [FAILURE_LABEL],
            },
        )
        return response.json()["number"]

    def comment_on_issue(self, issue_number: int, body: str) -> None:
        self._request("POST", f"/repos/{self.repo}/issues/{issue_number}/comments", json={"body": body})

    def close_issue(self, issue_number: int) -> None:
        self.comment_on_issue(issue_number, "The pipeline ran successfully — closing this failure issue.")
        self._request("PATCH", f"/repos/{self.repo}/issues/{issue_number}", json={"state": "closed"})

    def handle_run_outcome(self, abort_reason: str | None) -> str:
        """Orchestrates the full open/comment/close flow for one pipeline
        run and returns a human-readable summary of what it did."""
        existing = self.find_open_failure_issue()
        action = decide_action(existing, abort_reason)

        if action is Action.CREATE:
            number = self.create_failure_issue(abort_reason)
            return f"Opened failure issue #{number}: {abort_reason}"
        if action is Action.COMMENT:
            self.comment_on_issue(existing, f"Pipeline aborted again on a later run.\n\n**Reason:** {abort_reason}")
            return f"Commented on existing failure issue #{existing}: {abort_reason}"
        if action is Action.CLOSE:
            self.close_issue(existing)
            return f"Closed failure issue #{existing}"
        return "No open failure issue and no abort — nothing to do."
