from __future__ import annotations

import sys
import unittest
from pathlib import Path
from unittest.mock import patch

sys.path.insert(0, str(Path(__file__).resolve().parent))
import slack  # noqa: E402


class FakeClock:
    def __init__(self) -> None:
        self.now = 0.0
        self.sleeps: list[float] = []

    def monotonic(self) -> float:
        return self.now

    def sleep(self, seconds: float) -> None:
        self.sleeps.append(seconds)
        self.now += seconds


class PollingThrottleTests(unittest.TestCase):
    def test_wait_for_throttles_failed_polls(self) -> None:
        clock = FakeClock()
        calls = 0

        def fake_ab_eval(_js: str, cdp: int = 9222) -> str:
            nonlocal calls
            calls += 1
            clock.now += 0.001
            return "null"

        with (
            patch.object(slack, "ab_eval", side_effect=fake_ab_eval),
            patch.object(slack.time, "monotonic", side_effect=clock.monotonic),
            patch.object(slack.time, "sleep", side_effect=clock.sleep),
        ):
            result = slack.wait_for("ignored", timeout=0.25)

        self.assertIsNone(result)
        self.assertLessEqual(calls, 4)
        self.assertGreaterEqual(len(clock.sleeps), 2)

    def test_wait_for_ref_throttles_failed_polls(self) -> None:
        clock = FakeClock()
        calls = 0

        def fake_ab(*_args: str, cdp: int = 9222) -> str:
            nonlocal calls
            calls += 1
            clock.now += 0.001
            return 'button "Search" ref=e1'

        with (
            patch.object(slack, "ab", side_effect=fake_ab),
            patch.object(slack.time, "monotonic", side_effect=clock.monotonic),
            patch.object(slack.time, "sleep", side_effect=clock.sleep),
        ):
            ref, snapshot = slack.wait_for_ref(r'button "Wanted"', timeout=0.25)

        self.assertIsNone(ref)
        self.assertEqual(snapshot, 'button "Search" ref=e1')
        self.assertLessEqual(calls, 4)
        self.assertGreaterEqual(len(clock.sleeps), 2)


class SearchInputTests(unittest.TestCase):
    def test_open_search_bar_ignores_filter_comboboxes(self) -> None:
        snapshot = "\n".join([
            '- button "Search: policy-bot: master" [ref=e6]',
            '- combobox "Filter sources" [expanded=false, ref=e46]: Messages',
            '- combobox "Sort messages" [expanded=false, ref=e18]: Sort: Most relevant (default)',
        ])

        ab_calls: list[tuple[str, ...]] = []

        def fake_ab(*args: str, cdp: int = 9222) -> str:
            ab_calls.append(args)
            if args == ("snapshot", "-i"):
                return snapshot
            if args == ("click", "@e6"):
                return ""
            raise AssertionError(f"unexpected ab call: {args}")

        with (
            patch.object(slack, "ab", side_effect=fake_ab),
            patch.object(slack, "wait_for_ref", return_value=("e6", "- combobox \"Query\" [ref=e6]")),
        ):
            ref = slack._open_search_bar(9222)

        self.assertEqual(ref, "e6")
        self.assertIn(("click", "@e6"), ab_calls)


if __name__ == "__main__":
    unittest.main()
