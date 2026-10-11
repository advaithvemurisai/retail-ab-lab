import json
import math
import subprocess
import sys
from dataclasses import asdict
from pathlib import Path

import numpy as np
import pytest

pytest.importorskip("fastapi")
from fastapi.testclient import TestClient

from retaillab.analysis import Assumptions, analyze
from retaillab.api import create_app
from retaillab.data import demo_email
from retaillab.finance import load_margins
from retaillab.power import required_total_n
from retaillab.webdata import build_readout

SRC = Path(__file__).parents[1] / "src"
DEMO = demo_email()
# Round-trip through JSON, as the deployed function reads it from readout.json.
READOUT = json.loads(json.dumps(build_readout(DEMO, "demo", load_margins(force_demo=True), placebo_shuffles=3)))
CLIENT = TestClient(create_app(readout=READOUT))
CASES = [
    Assumptions(gross_margin=0.5),
    Assumptions(variant="mens", gross_margin=0.3),
    Assumptions(variant="womens", gross_margin=0.1, use_cuped=False),
    Assumptions(gross_margin=0.5, contact_cost=2.0),
    Assumptions(gross_margin=0.5, contact_cost=0.0),
    Assumptions(gross_margin=0.4, minimum_roi=2.0, weekly_customers=1_000),
]


def query(a: Assumptions) -> dict:
    return {
        "variant": a.variant, "margin": a.gross_margin, "cost": a.contact_cost,
        "min_roi": a.minimum_roi, "weekly": a.weekly_customers, "cuped": a.use_cuped,
    }


@pytest.mark.parametrize("a", CASES, ids=lambda a: str(asdict(a)))
def test_api_readout_matches_analyze(a):
    response = CLIENT.get("/api/readout", params=query(a))
    assert response.status_code == 200
    got = response.json()["readouts"][a.variant]
    expected = analyze(DEMO, a)
    assert got["verdict"] == json.loads(json.dumps(asdict(expected.verdict)))
    for key in ("revenue_lift", "break_even_lift", "planned_lift", "power", "required_n"):
        assert np.isclose(got[key], getattr(expected, key), rtol=1e-12)
    for key, value in expected.economics.items():
        assert got["economics"][key] is None if not math.isfinite(value) else np.isclose(got["economics"][key], value)
    for key, value in expected.contribution.items():
        assert np.isclose(got["contribution"][key], value, rtol=1e-12)
    assert got["additional_weeks"] == expected.additional_weeks


def test_api_serves_every_variant_and_table():
    body = CLIENT.get("/api/readout", params={"margin": 0.5}).json()
    assert set(body["readouts"]) == {"any", "mens", "womens"}
    assert len(body["sectors"]) == 3
    assert body["promotion"]["decision"] in {"roll_out", "lean", "send_neither"}
    assert len(body["mart_pnl"]) == 6


def test_api_targeting_fills_the_budget_from_the_top():
    body = CLIENT.get("/api/targeting", params={"margin": 0.5, "by": "channel", "cap": 5_000}).json()
    assert body["customers"] <= 5_000
    returns = [row["profit_per_dollar"] for row in body["rows"]]
    assert returns == sorted(returns, reverse=True)
    assert all(row["send_count"] == 0 for row in body["rows"] if row["profit_per_dollar"] <= 0)


def test_api_planning_matches_power_module():
    block = READOUT["variants"]["any"]
    body = CLIENT.get("/api/planning", params={"margin": 0.5, "lift": 0.2, "power": 0.9, "share": 0.5}).json()
    delta = 0.2 * block["baseline_revenue"]
    assert body["n_cuped"] == required_total_n(delta, block["pooled_sd"]["cuped"], 0.5, 0.05, 0.9)
    assert len(body["curve"]) == 60


def test_api_rejects_bad_assumptions():
    assert CLIENT.get("/api/readout", params={"margin": 0}).status_code == 422
    assert CLIENT.get("/api/readout", params={"variant": "sms"}).status_code == 422
    assert CLIENT.get("/api/targeting", params={"by": "colour", "cap": 10}).status_code == 422


def test_api_runs_without_the_scientific_stack():
    """The Vercel function bundles only FastAPI, so the API must not import pandas or scipy."""
    check = (
        "import sys; import retaillab.api; "
        "heavy = {'pandas', 'numpy', 'scipy', 'statsmodels', 'duckdb'} & set(sys.modules); "
        "assert not heavy, heavy"
    )
    subprocess.run([sys.executable, "-c", check], check=True, env={"PYTHONPATH": str(SRC)})
