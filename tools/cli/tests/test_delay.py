from __future__ import annotations

from locobox_cli.domain.delay import DelayPolicy


def test_delay_in_range() -> None:
    d = DelayPolicy(1.0, 2.0)
    for _ in range(20):
        v = d.next_seconds()
        assert 1.0 <= v <= 2.0
