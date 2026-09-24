"""Pure business verdict rules."""

from __future__ import annotations

import math
from dataclasses import dataclass


def format_roi(roi: float) -> str:
    """ROI is undefined when the campaign costs nothing to send."""
    return f"{roi:+.0%}" if math.isfinite(roi) else "n/a (no e-mail cost)"


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
    alpha: float = 0.05,
    chance_of_loss: float = 0.0,
) -> Verdict:
    """Rules are checked in order: trust, harm, economics, evidence."""
    if validity_failed:
        return Verdict(
            "DON'T TRUST",
            "invalid",
            ("Arm sizes do not match the designed split (sample ratio mismatch).",),
            "Find the assignment or logging fault and rerun the test.",
        )
    if primary_p < alpha and primary_lift < 0:
        return Verdict(
            "DON'T SHIP",
            "danger",
            (f"Revenue per customer is significantly lower ({primary_lift:+.1%}).",),
            "Keep the current experience.",
        )
    if contribution_high < 0:
        return Verdict(
            "DON'T SHIP",
            "danger",
            ("Even the optimistic end of the contribution interval loses money.",),
            "Do not roll out a money-losing campaign.",
        )
    if segment_harm:
        return Verdict(
            "DON'T SHIP",
            "danger",
            ("At least one customer segment is significantly worse off after BH correction.",),
            "Investigate the harmed segment before rollout.",
        )
    if primary_p < alpha and primary_lift > 0:
        if roi >= minimum_roi:
            reasons = (
                f"Revenue per customer is significantly higher ({primary_lift:+.1%}).",
                f"ROI of {roi:+.0%} clears the {minimum_roi:+.0%} hurdle."
                if math.isfinite(roi)
                else "The e-mail costs nothing to send, so any profitable lift clears the hurdle.",
            )
            if chance_of_loss > 0.1:
                return Verdict(
                    "SHIP",
                    "success",
                    (*reasons, f"There is still a {chance_of_loss:.0%} chance it loses money."),
                    "Roll out to a holdout-backed share first and watch contribution.",
                )
            return Verdict("SHIP", "success", reasons, "Roll out with monitoring.")
        return Verdict(
            "DON'T SHIP",
            "danger",
            (
                f"Revenue per customer is significantly higher ({primary_lift:+.1%}),",
                f"but ROI of {roi:+.0%} misses the {minimum_roi:+.0%} hurdle.",
            ),
            "Cut contact cost or target higher-return segments, then retest.",
        )
    if power >= 0.8:
        return Verdict(
            "DON'T SHIP",
            "danger",
            (f"No significant lift, and the test had {power:.0%} power to detect break-even.",),
            "Keep the current experience.",
        )
    return Verdict(
        "KEEP TESTING",
        "warning",
        (
            "The evidence is not decisive yet.",
            f"Power to detect a break-even lift is {power:.0%}, below the 80% target.",
        ),
        f"Run about {max(1, additional_weeks)} more week(s) or improve sensitivity.",
        max(1, additional_weeks),
    )
