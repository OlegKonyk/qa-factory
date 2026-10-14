"""Shared test setup: no test shows a desktop notification or posts anywhere when a run stops."""

import pytest

from factory import driver


@pytest.fixture(autouse=True)
def _no_notifications(monkeypatch):
    monkeypatch.setattr(driver, "NOTIFY", lambda *args, **kwargs: [])
