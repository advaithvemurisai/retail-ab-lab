"""Pure business verdict rules."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Verdict:
    label: str
    tone: str
    reasons: tuple[str, ...]
    next_step: str
    additional_weeks: int = 0


def decide(
    *,
    validity_failed: bool,
    primary_lift: float,
    primary_p: float,
    contribution_low: float,
    contribution_high: float,
    segment_harm: bool = False,
    roi: float = 0.0,
    minimum_roi: float = 0.0,
    power: float = 0.0,
    additional_weeks: int = 0,
) -> Verdict:
    if validity_failed:
        return Verdict(
            "DON'T TRUST",
            "invalid",
            ("The randomized split is imbalanced.",),
            "Fix assignment and rerun the test.",
        )
    if primary_p < 0.05 and primary_lift < 0:
        return Verdict(
            "DON'T SHIP",
            "danger",
            ("The primary outcome is significantly lower.",),
            "Keep the current experience.",
        )
    if contribution_high < 0:
        return Verdict(
            "DON'T SHIP",
            "danger",
            ("The full contribution interval is below zero.",),
            "Do not roll out a money-losing campaign.",
        )
    if segment_harm:
        return Verdict(
            "DON'T SHIP",
            "danger",
            ("A key segment has significant harm beyond tolerance.",),
            "Investigate the harmed segment before rollout.",
        )
    if primary_p < 0.05 and primary_lift > 0 and roi >= minimum_roi:
        return Verdict(
            "SHIP",
            "success",
            (
                "The primary outcome is significantly higher.",
                "The incremental economics clear the action threshold.",
            ),
            "Roll out with monitoring.",
        )
    if power >= 0.8:
        return Verdict(
            "DON'T SHIP",
            "danger",
            ("The result is null with enough power to detect the planned effect.",),
            "Keep the current experience.",
        )
    return Verdict(
        "KEEP TESTING",
        "warning",
        ("The evidence is not decisive yet.", f"Power is {power:.0%}, below the 80% target."),
        "Run longer or improve sensitivity.",
        max(1, additional_weeks),
    )
