from collections.abc import Iterator

import pytest

from serena.dashboard import SerenaDashboardAPI


@pytest.fixture(autouse=True)
def disable_dashboard_background_network() -> Iterator[None]:
    """
    SerenaDashboardAPI queries GitHub (news) and PyPI (newer version check) from background threads
    on construction. Tests must not depend on network access, so disable both; a test that needs
    either result should set the corresponding attribute on the instance directly.

    Uses a private MonkeyPatch rather than the ``monkeypatch`` fixture: requesting the shared fixture
    from an autouse fixture would set it up before ``setup_method``, so a test's own patches would
    still be active during ``teardown_method``.
    """
    with pytest.MonkeyPatch.context() as mp:
        mp.setattr(SerenaDashboardAPI, "_fetch_news", lambda self: None)
        mp.setattr(SerenaDashboardAPI, "_determine_newer_serena_version", lambda self: None)
        yield
