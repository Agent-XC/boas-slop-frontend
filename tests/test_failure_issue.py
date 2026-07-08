"""Tests for pipeline.failure_issue.decide_action() — the pure decision of
what to do with the scraper-failure issue, given the current open-issue
state and this run's abort_reason. Kept separate from the fixture-based
diff tests (#4) per issue #5's acceptance criteria; the HTTP-calling
functions in the same module are deliberately not covered here — verify
those with a manual smoke test against the real repo instead.
"""

from pipeline.failure_issue import Action, decide_action


def test_creates_when_aborting_with_no_open_issue():
    assert decide_action(existing_open_issue=None, abort_reason="count dropped") == Action.CREATE


def test_comments_when_aborting_with_an_open_issue_already():
    assert decide_action(existing_open_issue=42, abort_reason="count dropped") == Action.COMMENT


def test_closes_when_successful_with_an_open_issue():
    assert decide_action(existing_open_issue=42, abort_reason=None) == Action.CLOSE


def test_noop_when_successful_with_no_open_issue():
    assert decide_action(existing_open_issue=None, abort_reason=None) == Action.NOOP
